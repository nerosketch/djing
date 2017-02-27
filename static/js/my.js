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


// SelectAjax
(function ($) {
	$.fn.selectajax = function (opt) {

		var settings = $.extend( {
			url		 : '/api'
		}, opt);

		var selectbtn = this.children('button.selectajax-btn');
		var selectinp = this.children('input[type=text].selectajax-inp');
		var selecthid = this.children('input[type=hidden].selectajax-hid');
		var selectul  = this.children('ul.selectajax-ul');

		var selectajax_click = function(){
			var a = $(this).children('a');
			var hr = a.attr('href');
			var tx = a.text();
			selecthid.val(hr.substr(1));
			console.debug(tx);
			selectbtn.text(tx).removeClass('hidden');
			selectinp.addClass('hidden').val(tx);
		};

		var refresh = function(){
			$.getJSON(settings.url, {'s': this.value}, function (r) {
				selectul.empty();
				r.forEach(function (o) {
					var li = $('<li><a href="#' + o.id + '">' + o.name + ": " + o.fio + '</a></li>');
					selectul.append(li);
					li.on('click', selectajax_click)
				});
			});
		};

		selectinp.on('keyup', refresh).on('focusin',refresh);

		selectbtn.on('click',function(){
			selectinp.removeClass('hidden');
			$(this).addClass('hidden');
			selectinp.focus().trigger('click.bs.dropdown');
			return false;
		});

		selectul.children().on('click', selectajax_click);
	};
})(jQuery);


$(document).ready(function () {

	// ajax tabs
	$('.nav-tabs a').on('show.bs.tab', function (e) {
		var ct = $(e.target).attr('href');
		var remoteUrl = $(this).attr('data-tab-remote');
		if (remoteUrl !== '') {
			$(ct).load(remoteUrl);
		}
	});

	// Live html5 image preview
	if (window.File && window.FileReader && window.FileList && window.Blob) {
		$('input[type=file].live_review').on('change', function () {
			var reader = new FileReader();
			var img = $('img[alt=ava]')[0];
			reader.readAsDataURL(this.files[0]);
			reader.onload = function (e) {
				img.src = e.target.result;
			}
		});
	} else {
		var t = "Ваш браузер не поддерживает FileAPI";
		console.warn(t);
		alert(t);
	}


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


	$('div.selectajax').selectajax({
		url: '/abons/api/abon_filter'
	});

	$('[data-toggle=offcanvas]').click(function () {
		$('.row-offcanvas').toggleClass('active');
	});

    $('.btn-modal').on('click', function(){
        $.get(this.href, function(r){
            show_ModalMyContent(r);
        });
        return false;
    });

});
