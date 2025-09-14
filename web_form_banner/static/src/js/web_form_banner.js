odoo.define("web_form_banner.save_plus_load", function (require) {
    "use strict";
    var rpc = require("web.rpc");
    var FormController = require("web.FormController");

    function refreshBanners(ctrl) {
        // Support both old and new placeholders
        var $banners = ctrl.$('.o_form_view div[role="alert"][data-rule-id], .o_form_view div[role="alert"][data-wfb-rule-id]');
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
                var sev  = (res.severity || $b.data('default-severity') || 'danger');
                var html = (res.html || '');
                // Apply severity class if container uses the new class
                $b.attr('class', 'o_form_banner alert alert-' + sev);
                // Fill either the old <span> child or the container itself
                var $span = $b.find('> span');
                if ($span.length) {
                    $span.html(html);
                } else {
                    $b.html(html);
                }
                $b.show();
            });
        });
    }

    FormController.include({
        start: function () {
            var p = this._super.apply(this, arguments);
            var self = this;
            return p.then(function () {
                // one-time fetch when the form first appears
                refreshBanners(self);
            });
        },
        reload: function () {
            var p = this._super.apply(this, arguments);
            var self = this;
            return p.then(function () {
                // fetch again after any programmatic reload
                refreshBanners(self);
            });
        },
        saveRecord: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // fetch after successful save
                refreshBanners(self);
            });
        },
    });
});
