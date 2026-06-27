from datetime import datetime


class CursorPaginator:
    """
    Cursor-based pagination using timestamp cursors.
    """
    
    def __init__(self, queryset, cursor=None, page_size=50):
        self.queryset = queryset
        self.cursor = cursor
        self.page_size = page_size
    
    def paginate(self):
        """
        Paginate the queryset using cursor-based pagination.
        
        Returns:
            dict with 'results', 'next_cursor', 'has_more'
        """
        queryset = self.queryset
        
        # Apply cursor filter
        if self.cursor:
            try:
                cursor_time = datetime.fromisoformat(self.cursor)
                queryset = queryset.filter(created_at__lt=cursor_time)
            except (ValueError, TypeError):
                pass
        
        # Fetch one extra item to determine if there are more results
        items = list(queryset.order_by('-created_at')[:self.page_size + 1])
        
        # Determine if there are more results
        has_more = len(items) > self.page_size
        results = items[:self.page_size]
        
        # Calculate next cursor
        next_cursor = None
        if has_more and results:
            next_cursor = results[-1].created_at.isoformat()
        
        # Reverse to get chronological order
        results.reverse()
        
        return {
            'results': results,
            'next_cursor': next_cursor,
            'has_more': has_more
        }
