/* global window, module */

;(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
        typeof define === 'function' && define.amd ? define(factory) :
            global.Router = factory()
}(this, (function () {

    /**
     * Router
     *
     * @version: 1.2.7
     * @author Graidenix
     *
     * @constructor
     *
     * @param {object} options
     * @returns {Router}
     */
    function Router(options) {
        var settings = this._getSettings(options);


        this.notFoundHandler = settings.page404;
        this.mode = (!window.history || !window.history.pushState) ? "hash" : settings.mode;
        this.root = settings.root === "/" ? "/" : "/" + this._trimSlashes(settings.root) + "/";
        this.beforeHook = settings.hooks.before;
        this.securityHook = settings.hooks.secure;

        this.routes = [];
        if (settings.routes && settings.routes.length > 0) {
            var _this = this;
            settings.routes.forEach(function (route) {
                _this.add(route.rule, route.handler, route.options);
            });
        }

        this._pageState = null;
        this._currentPage = null;
        this._skipCheck = false;
        this._action = null;

        if (this.mode === "hash") {
            this._historyStack = [];
            this._historyIdx = 0;
            this._historyState = "add"
        }

        return this;
    }

    /**
     * Define Router Page
     *
     * @param {string} uri
     * @param {object} query
     * @param {Array} params
     * @param {object} state
     * @param {object} options
     *
     * @constructor
     */
    Router.Page = function (uri, query, params, state, options) {
        this.uri = uri || "";
        this.query = query || {};
        this.params = params || [];
        this.state = state || null;
        this.options = options || {};
    };

    /**
     * Sanitize options and add default values
     *
     * @param {object} options
     * @returns {object}
     * @private
     */
    Router.prototype._getSettings = function (options) {
        var settings = {};
        var defaults = {
            routes: [],
            mode: "history",
            root: "/",
            hooks: {
                "before": function () {
                },
                "secure": function () {
                    return true;
                }
            },
            page404: function (page) {
                console.error({
                    page: page,
                    message: "404. Page not found"
                });
            }
        };

        options = options || {};
        ["routes", "mode", "root", "page404"].forEach(function (key) {
            settings[key] = options[key] || defaults[key];
        });

        settings.hooks = Object.assign({}, defaults.hooks, options.hooks || {});

        return settings;
    };

    /**
     * Get URI for Router "history" mode
     *
     * @private
     * @returns {string}
     */
    Router.prototype._getHistoryFragment = function () {
        var fragment = decodeURI(window.location.pathname);
        if (this.root !== "/") {
            fragment = fragment.replace(this.root, "");
        }
        return this._trimSlashes(fragment);
    };

    /**
     * Get URI for router "hash" mode
     *
     * @private
     * @returns {string}
     */
    Router.prototype._getHashFragment = function () {
        var hash = window.location.hash.substr(1).replace(/(\?.*)$/, "");
        return this._trimSlashes(hash);
    };

    /**
     * Get current URI
     *
     * @private
     * @returns {string}
     */
    Router.prototype._getFragment = function () {
        if (this.mode === "history") {
            return this._getHistoryFragment();
        } else {
            return this._getHashFragment();
        }
    };

    /**
     * Trim slashes for path
     *
     * @private
     * @param {string} path
     * @returns {string}
     */
    Router.prototype._trimSlashes = function (path) {
        if (typeof path !== "string") {
            return "";
        }
        return path.toString().replace(/\/$/, "").replace(/^\//, "");
    };

    /**
     * 404 Page Handler
     *
     * @private
     */
    Router.prototype._page404 = function (path) {
        this._currentPage = new Router.Page(path);
        this.notFoundHandler(path);
    };

    /**
     * Convert the string route rule to RegExp rule
     *
     * @param {string} route
     * @returns {RegExp}
     * @private
     */
    Router.prototype._parseRouteRule = function (route) {
        if (typeof route !== "string") {
            return route;
        }
        var uri = this._trimSlashes(route);
        var rule = uri
            .replace(/([\\\/\-\_\.])/g, "\\$1")
            .replace(/\{[a-zA-Z]+\}/g, "(:any)")
            .replace(/\:any/g, "[\\w\\-\\_\\.]+")
            .replace(/\:word/g, "[a-zA-Z]+")
            .replace(/\:num/g, "\\d+");

        return new RegExp("^" + rule + "$", "i");
    };

    /**
     * Parse query string and return object for it
     *
     * @param {string} query
     * @returns {object}
     * @private
     */
    Router.prototype._parseQuery = function (query) {
        var _query = {};
        if (typeof query !== "string") {
            return _query;
        }

        if (query[0] === "?") {
            query = query.substr(1);
        }

        this._queryString = query;
        query.split("&").forEach(function (row) {
            var parts = row.split("=");
            if (parts[0] !== "") {
                if (parts[1] === undefined) {
                    parts[1] = true;
                }
                _query[decodeURIComponent(parts[0])] = parts[1];
            }
        });
        return _query;
    };

    /**
     * Get query for `history` mode
     *
     * @returns {Object}
     * @private
     */
    Router.prototype._getHistoryQuery = function () {
        return this._parseQuery(window.location.search);
    };

    /**
     * Get query for `hash` mode
     *
     * @returns {Object}
     * @private
     */
    Router.prototype._getHashQuery = function () {
        var index = window.location.hash.indexOf("?");
        var query = (index !== -1) ? window.location.hash.substr(index) : "";
        return this._parseQuery(query);
    };

    /**
     * Get query as object
     *
     * @private
     * @returns {Object}
     */
    Router.prototype._getQuery = function () {
        if (this.mode === "history") {
            return this._getHistoryQuery();
        } else {
            return this._getHashQuery();
        }
    };

    /**
     * Add route to routes list
     *
     * @param {string|RegExp} rule
     * @param {function} handler
     * @param {{}} options
     * @returns {Router}
     */
    Router.prototype.add = function (rule, handler, options) {
        this.routes.push({
            rule: this._parseRouteRule(rule),
            handler: handler,
            options: options
        });
        return this;
    };

    /**
     * Remove a route from routes list
     *
     * @param param
     * @returns {Router}
     */
    Router.prototype.remove = function (param) {
        var _this = this;
        if (typeof param === "string") {
            param = this._parseRouteRule(param).toString();
        }
        this.routes.some(function (route, i) {
            if (route.handler === param || route.rule.toString() === param) {
                _this.routes.splice(i, 1);
                return true;
            }
            return false;
        });

        return this;
    };

    /**
     * Reset the state of Router
     *
     * @returns {Router}
     */
    Router.prototype.reset = function () {
        this.routes = [];
        this.mode = null;
        this.root = "/";
        this._pageState = {};
        this.removeUriListener();

        return this;
    };

    /**
     * Add current page in history stack
     * @private
     */
    Router.prototype._pushHistory = function () {
        var _this = this,
            fragment = this._getFragment();

        if (this.mode === "hash") {
            if (this._historyState === "add") {
                if (this._historyIdx !== this._historyStack.length - 1) {
                    this._historyStack.splice(this._historyIdx + 1);
                }

                this._historyStack.push({
                    path: fragment,
                    state: _this._pageState
                });

                this._historyIdx = this._historyStack.length - 1;
            }
            this._historyState = "add";
        }
    };

    /**
     *
     * @param asyncRequest boolean
     * @returns {PromiseResult<boolean> | boolean}
     * @private
     */
    Router.prototype._unloadCallback = function (asyncRequest) {
        var result;

        if (this._skipCheck) {
            return asyncRequest ? Promise.resolve(true) : true;
        }

        if (this._currentPage && this._currentPage.options && this._currentPage.options.unloadCb) {
            result = this._currentPage.options.unloadCb(this._currentPage, asyncRequest);
            if (!asyncRequest || result instanceof Promise) {
                return result;
            }
            return result ? Promise.resolve(result) : Promise.reject(result);
        } else {
            return asyncRequest ? Promise.resolve(true) : true;
        }
    };

    /**
     * Check if router has the action for current path
     *
     * @returns {boolean}
     * @private
     */
    Router.prototype._findRoute = function () {
        var _this = this,
            fragment = this._getFragment();

        return this.routes.some(function (route) {
            var match = fragment.match(route.rule);
            if (match) {
                match.shift();
                var query = _this._getQuery();
                var page = new Router.Page(fragment, query, match, _this._pageState, route.options);

                if (!_this.securityHook(page)) {
                    return false;
                }

                _this._currentPage = page;
                if (_this._skipCheck) {
                    _this._skipCheck = false;
                    return true;
                }
                _this.beforeHook(page);
                route.handler.apply(page, match);
                _this._pageState = null;

                window.onbeforeunload = function (ev) {
                    if (_this._unloadCallback(false)) {
                        return;
                    }
                    ev.returnValue = true;
                    return true;
                };

                return true;
            }
            return false;
        });
    };

    /**
     *
     */
    Router.prototype._treatAsync = function () {
        var result;

        result = this._currentPage.options.unloadCb(this._currentPage, true);
        if (!(result instanceof Promise)) {
            result = result ? Promise.resolve(result) : Promise.reject(result);
        }

        result
            .then(this._processUri.bind(this))
            .catch(this._resetState.bind(this));
    };

    /**
     *
     * @private
     */
    Router.prototype._resetState = function () {
        this._skipCheck = true;
        this.navigateTo(this._current, this._currentPage.state, true);
    };

    /**
     * Replace current page with new one
     */
    Router.prototype._processUri = function () {
        var fragment = this._getFragment(),
            found;

        this._current = fragment;
        this._pushHistory();

        found = this._findRoute.call(this);
        if (!found) {
            this._page404(fragment);
        }
    };

    /**
     * Check the URL and execute handler for its route
     *
     * @returns {Router}
     */
    Router.prototype.check = function () {
        if (this._skipCheck) return this;

        // if page has unload cb treat as promise
        if (this._currentPage && this._currentPage.options && this._currentPage.options.unloadCb) {
            this._treatAsync();
        } else {
            this._processUri();
        }
        return this;
    };

    /**
     * Add the URI listener
     *
     * @returns {Router}
     */
    Router.prototype.addUriListener = function () {
        if (this.mode === "history") {
            window.onpopstate = this.check.bind(this);
        } else {
            window.onhashchange = this.check.bind(this);
        }

        return this;
    };

    /**
     * Remove the URI listener
     *
     * @returns {Router}
     */
    Router.prototype.removeUriListener = function () {
        window.onpopstate = null;
        window.onhashchange = null;
        return this;
    };

    /**
     * Redirect to a page with replace state
     *
     * @param {string} path
     * @param {object} state
     * @param {boolean} silent
     *
     * @returns {Router}
     */
    Router.prototype.redirectTo = function (path, state, silent) {
        path = this._trimSlashes(path) || "";
        this._pageState = state || null;
        this._skipCheck = !!silent;

        if (this.mode === "history") {
            history.replaceState(state, null, this.root + this._trimSlashes(path));
            return this.check();
        } else {
            this._historyIdx--;
            window.location.hash = path;
        }
        return this;
    };

    /**
     * Navigate to a page
     *
     * @param {string} path
     * @param {object} state
     * @param {boolean} silent
     *
     * @returns {Router}
     */
    Router.prototype.navigateTo = function (path, state, silent) {
        path = this._trimSlashes(path) || "";
        this._pageState = state || null;
        this._skipCheck = !!silent;

        if (this.mode === "history") {
            history.pushState(state, null, this.root + this._trimSlashes(path));
            return this.check();
        } else {
            window.location.hash = path;
        }
        return this;
    };

    /**
     * Refresh page with recall route handler
     * @returns {Router}
     */
    Router.prototype.refresh = function () {
        if (!this._currentPage) {
            return this;
        }
        var path = this._currentPage.uri + "?" + this._queryString;
        return this.navigateTo(path, this._currentPage.state);
    };

    /**
     * Go Back in browser history
     * Simulate "Back" button
     *
     * @returns {Router}
     */
    Router.prototype.back = function () {
        if (this.mode === "history") {
            window.history.back();
            return this;
        }

        return this.go(this._historyIdx - 1);
    };

    /**
     * Go Forward in browser history
     * Simulate "Forward" button
     *
     * @returns {Router}
     */
    Router.prototype.forward = function () {
        if (this.mode === "history") {
            window.history.forward();
            return this;
        }

        return this.go(this._historyIdx + 1);
    };

    /**
     * Go to a specific history page
     *
     * @param {number} count
     * @returns {Router}
     */
    Router.prototype.go = function (count) {
        if (this.mode === "history") {
            window.history.go(count);
            return this;
        }

        var page = this._historyStack[count];
        if (!page) {
            return this;
        }

        this._historyIdx = count;
        this._historyState = "hold";
        return this.navigateTo(page.path, page.state);
    };

    return Router;
})));