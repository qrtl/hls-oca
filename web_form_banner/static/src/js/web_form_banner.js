// web_form_banner/static/src/js/web_form_banner.js
odoo.define("web_form_banner.save_plus_load", function (require) {
    "use strict";
    var rpc = require("web.rpc");
    var FormController = require("web.FormController");

    function refreshBanners(ctrl) {
        var $banners = ctrl.$('.o_form_view div[role="alert"][data-wfb-rule-id]');
        var state = ctrl.model.get(ctrl.handle);
        var resId = state && state.res_id;
        if (!resId || !$banners.length) return;

        $banners.each(function () {
            var $b = $(this);
            rpc.query({
                model: "web_form_banner.rule",
                method: "render_message",
                args: [parseInt($b.data("wfb-rule-id")), $b.data("wfb-model"), resId],
            }).then(function (text) {
                // $b.find("> span").html(text || "");
                text = text || '';
                var hasContent = /\S/.test(text);   // any non-whitespace?
                if (hasContent) {
                    $b.show();
                    $b.find('> span').html(text);
                } else {
                    $b.hide();
                    $b.find('> span').empty();
                }
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
