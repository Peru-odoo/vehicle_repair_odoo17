/** @odoo-module */

import PublicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement } from "@web/core/utils/render";


   PublicWidget.registry.NewElements = PublicWidget.Widget.extend({
        selector:'.repair_snippet',
        start: function(){
        var self = this;

        jsonrpc('/latest_record').then(function(data){
            if (data.length > 0){
                data[0].is_active = true
                self.$el.find('#latest_record').html(renderToElement("vehicle_repair.repair_snipped_carousel", {data: data}))
            }
        });
        return this._super(...arguments)
        },
   })