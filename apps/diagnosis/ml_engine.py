import io
import json
import math
import time
from pathlib import Path

from django.conf import settings


_ENGINE = None

# Dog-detection prompts — identical to the Kaggle notebook.
POSITIVE_PROMPTS = [
    'a dog',
    'a canine',
    'a domestic dog',
    'a puppy',
    'a pet dog',
]
NEGATIVE_PROMPTS = [
    'a cat',
    'a horse',
    'a bird',
    'a rabbit',
    'an object',
]

IMAGE_SIZE = 380
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def _build_model_classes(torch, nn, F, torchvision):
    """Build the ArcFace model classes (matches the training/inference notebook)."""

    class ArcMarginProduct(nn.Module):
        def __init__(self, in_features, out_features, s=30.0, m=0.5):
            super().__init__()
            self.in_features = in_features
            self.out_features = out_features
            self.s = s
            self.m = m
            self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
            nn.init.xavier_uniform_(self.weight)
            self.cos_m = math.cos(m)
            self.sin_m = math.sin(m)
            self.th = math.cos(math.pi - m)
            self.mm = math.sin(math.pi - m) * m

        def forward(self, embeddings, labels):
            cosine = F.linear(F.normalize(embeddings), F.normalize(self.weight))
            sine = torch.sqrt(torch.clamp(1.0 - torch.pow(cosine, 2), min=1e-7))
            phi = cosine * self.cos_m - sine * self.sin_m
            phi = torch.where(cosine > self.th, phi, cosine - self.mm)
            one_hot = torch.zeros_like(cosine)
            one_hot.scatter_(1, labels.view(-1, 1).long(), 1.0)
            output = (one_hot * phi) + ((1.0 - one_hot) * cosine)
            return output * self.s

    class EfficientNetArcFace(nn.Module):
        def __init__(self, num_classes, embed_dim=256, s=30.0, m=0.5):
            super().__init__()
            self.num_classes = num_classes
            self.embed_dim = embed_dim
            backbone = torchvision.models.efficientnet_b4(weights=None)
            in_features = backbone.classifier[1].in_features
            backbone.classifier = nn.Identity()
            self.backbone = backbone
            self.embedding_layer = nn.Sequential(
                nn.Linear(in_features, embed_dim),
                nn.BatchNorm1d(embed_dim),
            )
            self.arcface_head = ArcMarginProduct(embed_dim, num_classes, s=s, m=m)

        def forward(self, x, labels=None):
            features = self.backbone(x)
            embeddings = self.embedding_layer(features)
            embeddings = F.normalize(embeddings, p=2, dim=1)
            if labels is not None:
                logits = self.arcface_head(embeddings, labels)
                return logits, embeddings
            return embeddings

    return EfficientNetArcFace


class DiagnosisMLEngine:
    artifact_names = {
        'checkpoint': 'best_arcface_b4.pth',
        'prototypes': 'prototypes.npy',
        'threshold': 'threshold.json',
        'classes': 'class_names.json',
    }

    def __init__(self):
        self.loaded = False
        self.load_error = ''
        self.device = None
        self.model = None
        self.clip_model = None
        self.clip_preprocess = None
        self.clip_tokenizer = None
        self.class_names = []
        self.prototypes = None
        self.threshold = 0.0
        self.transforms = None
        self.torch = None
        self.F = None
        self.np = None
        self.Image = None

    def load_models(self):
        if self.loaded or self.load_error:
            return self.loaded

        try:
            import numpy as np
            import open_clip
            import torch
            import torch.nn as nn
            import torch.nn.functional as F
            import torchvision
            from PIL import Image
            from torchvision import transforms
        except ImportError as exc:
            self.load_error = f'ML dependencies are not installed: {exc}'
            return False

        models_dir = Path(getattr(settings, 'ML_MODELS_DIR', settings.BASE_DIR / 'ml_models'))
        missing = [
            filename for filename in self.artifact_names.values()
            if not (models_dir / filename).exists()
        ]
        if missing:
            self.load_error = f'Missing ML model artifacts in {models_dir}: {", ".join(missing)}'
            return False

        try:
            self.torch = torch
            self.F = F
            self.np = np
            self.Image = Image
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            with open(models_dir / self.artifact_names['classes'], encoding='utf-8') as fp:
                classes_payload = json.load(fp)
            self.class_names = classes_payload.get('class_names', classes_payload)

            with open(models_dir / self.artifact_names['threshold'], encoding='utf-8') as fp:
                threshold_payload = json.load(fp)
            self.threshold = float(threshold_payload.get('threshold', 0.0))

            # Prototypes are used RAW (no re-normalization) — matches the notebook.
            self.prototypes = np.load(models_dir / self.artifact_names['prototypes']).astype('float32')

            checkpoint = torch.load(
                models_dir / self.artifact_names['checkpoint'],
                map_location=self.device,
            )
            num_classes = int(checkpoint.get('num_classes', len(self.class_names)))
            embed_dim = int(checkpoint.get('embed_dim', self.prototypes.shape[1]))
            arc_s = float(checkpoint.get('arc_s', 30.0))
            arc_m = float(checkpoint.get('arc_m', 0.5))

            model_class = _build_model_classes(torch, nn, F, torchvision)
            self.model = model_class(num_classes=num_classes, embed_dim=embed_dim, s=arc_s, m=arc_m)
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device).eval()

            self.transforms = transforms.Compose([
                transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ])

            self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32',
                pretrained='openai',
            )
            self.clip_model = self.clip_model.to(self.device)
            self.clip_model.eval()
            self.clip_tokenizer = open_clip.get_tokenizer('ViT-B-32')
            self.loaded = True
            return True
        except Exception as exc:
            self.load_error = f'Unable to load ML models: {exc}'
            return False

    def predict(self, image_file_or_url):
        started_at = time.perf_counter()
        if not self.load_models():
            return self._unavailable_result(started_at)

        try:
            image = self._load_image(image_file_or_url)

            if not self._is_dog(image):
                return {
                    'success': False,
                    'is_dog': False,
                    'message': 'The uploaded image does not appear to contain a dog.',
                    'severity': 'LOW',
                    'risk_score': 0.0,
                    'predicted_diseases': [],
                    'inference_time_ms': self._elapsed_ms(started_at),
                    'model_version': getattr(settings, 'ML_MODEL_VERSION', '1.0.0'),
                }

            embedding = self._generate_embedding(image)
            scores = self.prototypes @ embedding
            best_index = int(scores.argmax())
            similarity = float(scores[best_index])
            disease_name = self.class_names[best_index] if best_index < len(self.class_names) else 'Unknown'

            order = scores.argsort()[::-1][:3]
            predictions = [
                {
                    'disease': self.class_names[int(idx)] if int(idx) < len(self.class_names) else 'Unknown',
                    'similarity': round(float(scores[int(idx)]), 4),
                }
                for idx in order
            ]

            if similarity < self.threshold:
                disease_name = 'Unknown'
                message = 'A dog was detected, but the condition similarity is below the confidence threshold.'
            else:
                message = 'Diagnosis completed successfully.'

            return {
                'success': True,
                'is_dog': True,
                'disease': disease_name,
                'similarity': round(similarity, 4),
                'threshold': round(self.threshold, 4),
                'severity': self._severity_for_similarity(similarity),
                'risk_score': min(max(similarity, 0.0), 1.0),
                'predicted_diseases': predictions,
                'message': message,
                'inference_time_ms': self._elapsed_ms(started_at),
                'model_version': getattr(settings, 'ML_MODEL_VERSION', '1.0.0'),
            }
        except Exception as exc:
            return {
                'success': False,
                'is_dog': False,
                'message': f'Diagnosis failed: {exc}',
                'severity': 'LOW',
                'risk_score': 0.0,
                'predicted_diseases': [],
                'inference_time_ms': self._elapsed_ms(started_at),
                'model_version': getattr(settings, 'ML_MODEL_VERSION', '1.0.0'),
            }

    def _load_image(self, image_file_or_url):
        if isinstance(image_file_or_url, str) and image_file_or_url.startswith(('http://', 'https://')):
            import requests
            response = requests.get(image_file_or_url, timeout=30)
            response.raise_for_status()
            return self.Image.open(io.BytesIO(response.content)).convert('RGB')
        if hasattr(image_file_or_url, 'read'):
            image_file_or_url.seek(0)
        return self.Image.open(image_file_or_url).convert('RGB')

    def _is_dog(self, image):
        torch = self.torch
        F = self.F
        with torch.no_grad():
            image_input = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            all_prompts = POSITIVE_PROMPTS + NEGATIVE_PROMPTS
            text_tokens = self.clip_tokenizer(all_prompts).to(self.device)

            image_features = self.clip_model.encode_image(image_input)
            text_features = self.clip_model.encode_text(text_tokens)
            image_features = F.normalize(image_features, dim=-1)
            text_features = F.normalize(text_features, dim=-1)

            similarities = (image_features @ text_features.T).squeeze(0)
            pos_score = similarities[:len(POSITIVE_PROMPTS)].mean().item()
            neg_score = similarities[len(POSITIVE_PROMPTS):].mean().item()
        return pos_score > neg_score

    def _generate_embedding(self, image):
        torch = self.torch
        with torch.no_grad():
            tensor = self.transforms(image).unsqueeze(0).to(self.device)
            embedding = self.model(tensor)
        embedding = embedding.squeeze(0).cpu().numpy().astype('float32')
        embedding = embedding / (self.np.linalg.norm(embedding) + 1e-8)
        return embedding

    def _severity_for_similarity(self, similarity):
        if similarity >= 0.85:
            return 'HIGH'
        if similarity >= 0.70:
            return 'MODERATE'
        return 'LOW'

    def _unavailable_result(self, started_at):
        return {
            'success': False,
            'is_dog': False,
            'message': self.load_error or 'AI diagnosis is unavailable.',
            'severity': 'LOW',
            'risk_score': 0.0,
            'predicted_diseases': [],
            'inference_time_ms': self._elapsed_ms(started_at),
            'model_version': getattr(settings, 'ML_MODEL_VERSION', '1.0.0'),
            'feature_unavailable': True,
        }

    def _elapsed_ms(self, started_at):
        return int((time.perf_counter() - started_at) * 1000)


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = DiagnosisMLEngine()
    return _ENGINE


def load_models():
    return get_engine().load_models()


def predict(image_file_or_url):
    return get_engine().predict(image_file_or_url)
