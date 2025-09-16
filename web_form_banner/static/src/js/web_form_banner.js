odoo.define("web_form_banner.save_plus_load", function (require) {
    "use strict";
    var rpc = require("web.rpc");
    var FormController = require("web.FormController");

    function refreshBanners(ctrl) {
        var $banners = ctrl.$('.o_form_view div[role="alert"][data-rule-id]');
        var state = ctrl.model.get(ctrl.handle);
        var resId = state && state.res_id;
        if (!resId || !$banners.length) return;

        $banners.each(function () {
            var $b = $(this);
            var ruleId = parseInt($b.data("rule-id") || $b.data("wfb-rule-id"));
            var model  = ($b.data("model") || $b.data("wfb-model") || ctrl.modelName);
            rpc.query({
                model: "web.form.banner.rule",
                method: "compute_message",
                args: [ruleId, model, resId],
            }).then(function (res) {
                res = res || {};
                if (!res.visible) {
                    $b.hide();
                    $b.find('> span').empty();
                    return;
                }
                var sev  = (res.severity || $b.data("default-severity") || "danger");
                var html = (res.html || "");
                // Apply severity class if container uses the new class
                $b.attr("class", "o_form_banner alert alert-" + sev);
                // Fill either the old <span> child or the container itself
                var $span = $b.find("> span");
                if ($span.length) {
                    $span.html(html);
                } else {
                    $b.html(html);
                }
                $b.show();
            });
        });
    }

    function withRefresh(ctrl, superFn, args) {
        var p = superFn.apply(ctrl, args);
        return p.then(function () {
            refreshBanners(ctrl);
        });
    }

    FormController.include({
        start: function () {
            return withRefresh(this, this._super, arguments);
        },
        reload: function () {
            return withRefresh(this, this._super, arguments);
        },
        saveRecord: function () {
            return withRefresh(this, this._super, arguments);
        },
        update: function (params, options) {
            return withRefresh(this, this._super, arguments);
        },
    });
});
