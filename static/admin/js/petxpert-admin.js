/**
 * PetXpert Admin — lightweight enhancements for django-unfold.
 */
(function () {
    'use strict';

    var DESKTOP_MIN_WIDTH = 1280;

    function getAlpineThemeData() {
        var html = document.documentElement;
        if (!html) return null;

        if (html._x_dataStack && html._x_dataStack.length) {
            return html._x_dataStack[0];
        }

        if (html.__x && html.__x.$data) {
            return html.__x.$data;
        }

        return null;
    }

    function readSidebarOpen(data) {
        if (!data) return true;
        if (typeof data.sidebarOpen === 'function') {
            return !!data.sidebarOpen();
        }
        return data.sidebarOpen !== false;
    }

    function writeSidebarOpen(data, isOpen) {
        if (!data) return;
        data.sidebarOpen = !!isOpen;
        if (window.innerWidth > DESKTOP_MIN_WIDTH) {
            localStorage.setItem('sidebarOpen', isOpen ? '1' : '0');
        }
    }

    function normalizeSidebarState() {
        var data = getAlpineThemeData();
        if (!data) return;
        if (typeof data.sidebarOpen === 'function') {
            data.sidebarOpen = readSidebarOpen(data);
        }
    }

    function patchUnfoldTheme() {
        if (typeof window.theme !== 'function' || window.theme.__petxpertPatched) {
            return;
        }

        var originalTheme = window.theme;

        window.theme = function (defaultTheme) {
            var data = originalTheme(defaultTheme);
            var lastViewportWidth = window.innerWidth;

            function syncSidebarFromStorage() {
                data.sidebarOpen =
                    localStorage.getItem('sidebarOpen') === '0' ? false : true;
            }

            data.sidebarToggle = function () {
                writeSidebarOpen(data, !readSidebarOpen(data));
            };

            var originalInit = data.init;
            data.init = function () {
                if (typeof originalInit === 'function') {
                    originalInit.call(this);
                }
                if (typeof data.sidebarOpen === 'function') {
                    data.sidebarOpen = readSidebarOpen(data);
                }
            };

            if (data.themeBindings) {
                data.themeBindings['x-resize.window'] = function () {
                    var width = window.innerWidth;
                    var crossedToMobile =
                        lastViewportWidth > DESKTOP_MIN_WIDTH && width <= DESKTOP_MIN_WIDTH;
                    var crossedToDesktop =
                        lastViewportWidth <= DESKTOP_MIN_WIDTH && width > DESKTOP_MIN_WIDTH;

                    if (width <= DESKTOP_MIN_WIDTH) {
                        // Only auto-close when shrinking from desktop to tablet/mobile.
                        if (crossedToMobile) {
                            data.sidebarOpen = false;
                        }
                    } else if (crossedToDesktop) {
                        syncSidebarFromStorage();
                    }

                    lastViewportWidth = width;
                };
            }

            return data;
        };

        window.theme.__petxpertPatched = true;
    }

    window.petxpertToggleSidebar = function (event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        var data = getAlpineThemeData();
        if (!data) return;

        writeSidebarOpen(data, !readSidebarOpen(data));
    };

    function patchLiveThemeInstance() {
        var data = getAlpineThemeData();
        if (!data || data.__petxpertSidebarPatched) {
            return;
        }

        data.sidebarToggle = function () {
            writeSidebarOpen(data, !readSidebarOpen(data));
        };

        if (typeof data.sidebarOpen === 'function') {
            data.sidebarOpen = readSidebarOpen(data);
        }

        data.__petxpertSidebarPatched = true;
    }

    patchUnfoldTheme();
    document.addEventListener('DOMContentLoaded', patchUnfoldTheme);
    document.addEventListener('alpine:init', patchUnfoldTheme);
    document.addEventListener('alpine:initialized', function () {
        patchLiveThemeInstance();
        normalizeSidebarState();
    });

    document.addEventListener('DOMContentLoaded', function () {
        normalizeSidebarState();

        document.body.classList.add('petxpert-admin-loaded');

        document.querySelectorAll('#result_list tbody tr').forEach(function (row) {
            row.classList.add('petxpert-table-row');
        });

        var messages = document.querySelectorAll('.messagelist li');
        messages.forEach(function (msg, index) {
            msg.classList.add('petxpert-toast');
            msg.style.animationDelay = (index * 0.1) + 's';
            setTimeout(function () {
                msg.classList.add('petxpert-toast-hide');
                setTimeout(function () { msg.remove(); }, 400);
            }, 5000);
        });
    });
})();
