(function ($){
    $.fn.cidr_validator = function(opts){
        var IP4_REG = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/s;
        var IP6_REG = /^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]d|1dd|[1-9]?d)(.(25[0-5]|2[0-4]d|1dd|[1-9]?d)){3}))|:)))(%.+)?$/s;
        var settings = $.extend( {
			res_label: this.find('.panel-title>span')
		}, opts);

        var net_inp = this.find('#id_network');
        var mask_inp = this.find('#id_mask');

        var validate_ip_by_key = function(){
            var v = this.value;
            if(v === undefined)
                return;
            var o = $(this).closest('.form-group-sm,.form-group');
            o.removeClass('has-error has-success');
            if(v.match(IP4_REG) !== null){
                mask_inp.val('24');
                o.addClass('has-success');
            }else
            if(v.match(IP6_REG) !== null){
                mask_inp.val('64');
                o.addClass('has-success');
            }else
                o.addClass('has-error');
        };
        var validate_ip_by_focus = function(){
            var v = this.value;
            if(v.includes('/')){
                var chunks = v.split('/');
                if(chunks[1] !== ""){
                    net_inp.val(chunks[0]);
                    mask_inp.val(chunks[1]);
                    settings.res_label.text(v);
                }
            }else {
                settings.res_label.text(v + '/' + mask_inp.val());
            }
            $(this).trigger('keyup');
        };
        net_inp.on('keyup focusin', validate_ip_by_key);
        net_inp.on('focusout', validate_ip_by_focus);

        var validate_mask = function(){

        };
        mask_inp.on('change', validate_mask);
    };
})(jQuery);


$(document).ready(function () {
    $('div.cidr-contain').cidr_validator();
});
