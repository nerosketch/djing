function show_ModalMyContent(content){
    $('#modContent').html(content);
	$('#modFrm').modal();
}
function show_Modal(title, content, type_class){
var cnt='<div class="modal-header '+type_class+'">' +
            '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>' +
            '<h4 class="modal-title"><span class="glyphicon glyphicon-warning-sign"></span>'+title+'</h4>' +
        '</div>' +
        '<div class="modal-body">'+content+'</div>' +
        '<div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal">Закрыть</button></div>';
	show_ModalMyContent(cnt);
}

function showErr(errContent) {show_Modal('Ошибка', errContent, 'warning');}
function showSuccess(errContent) {show_Modal('Успешно', errContent, 'success');}
function showPrimary(errContent) {show_Modal('Внимание!', errContent, 'primary');}

$(document).ajaxError(function (ev, jqXHR, ajaxSettings, thrownError) {
	//loaderShow(false);
	showErr(jqXHR.status + ': ' + jqXHR.statusText);
});



$(document).ready(function () {

	// Validate inputs of form
	$('input.form-control[pattern]').keyup(function () {
		var pr = $(this).closest('.form-group-sm,.form-group');
		pr.removeClass('has-success');
		pr.removeClass('has-error');
		pr.find('.form-control-feedback').remove();
		if ($(this)[0].checkValidity()) {
			pr.addClass('has-success');
			$(this).after('<span class="glyphicon glyphicon-ok form-control-feedback"></span>');
		} else {
			pr.addClass('has-error');
			$(this).after('<span class="glyphicon glyphicon-remove form-control-feedback"></span>');
		}
	});

	// autosave checkbox
	$('input[type=checkbox].autosave').on('click', function(){
		var data_url = $(this).attr('data-url');
		$.getJSON(data_url, {checked: this.checked});
	});

    $('.btn-modal').on('click', function(){
        $.get(this.href, function(r){
            show_ModalMyContent(r);
        });
        return false;
    });

});
