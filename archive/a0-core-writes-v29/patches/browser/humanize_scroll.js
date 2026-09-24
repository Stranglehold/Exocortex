// Scroll humanizer — adds natural variance to window.scrollBy / window.scrollTo
// Loaded as an additional browser init script by browser_agent.py
// Subtle ±8% jitter and object-form support.
(function () {
    if (window.__A0_scroll_humanized) return;
    window.__A0_scroll_humanized = true;

    var _nativeScrollBy = window.scrollBy.bind(window);
    var _nativeScrollTo = window.scrollTo.bind(window);

    function _jitter(v) {
        // ±8% natural variance with a small gaussian-like distribution
        var r = (Math.random() + Math.random() + Math.random()) / 3 - 0.5; // [-0.5, 0.5], roughly normal
        return Math.round(v * (1 + r * 0.16));
    }

    window.scrollBy = function (xOrOptions, y) {
        if (xOrOptions !== null && typeof xOrOptions === 'object') {
            var opts = Object.assign({}, xOrOptions);
            if (opts.top !== undefined) opts.top = _jitter(opts.top);
            if (opts.left !== undefined) opts.left = _jitter(opts.left);
            _nativeScrollBy(opts);
        } else {
            _nativeScrollBy(_jitter(xOrOptions || 0), _jitter(y || 0));
        }
    };

    window.scrollTo = function (xOrOptions, y) {
        if (xOrOptions !== null && typeof xOrOptions === 'object') {
            _nativeScrollTo(xOrOptions); // absolute position — don't jitter
        } else {
            _nativeScrollTo(xOrOptions || 0, y || 0);
        }
    };
})();
