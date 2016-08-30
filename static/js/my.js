function errShow(errContent){
    //window.history.back();

    $('#modContent').html('<div class="modal-header warning">\
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>\
    <h4 class="modal-title" id="myModalLabel"><span class="glyphicon glyphicon-warning-sign"></span>\
        Ошибка\
</h4>\
</div>\
<div class="modal-body">'+
    errContent
+'</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" data-dismiss="modal">Закрыть</button>\
</div>');
    $('#modFrm').modal();

}

$(document).ajaxError(function(ev, jqXHR, ajaxSettings, thrownError ){
    //loaderShow(false);
    errShow(jqXHR.status+': '+jqXHR.statusText);
});


$(document).ready(function(){

  // ajax tabs
  $('.nav-tabs a').on('show.bs.tab', function(e) {
    var ct = $(e.target).attr('href');
    var remoteUrl = $(this).attr('data-tab-remote');
    if (remoteUrl !== ''){
        $(ct).load(remoteUrl);
    }
  });

  // Live html5 image preview
  if(window.File && window.FileReader && window.FileList && window.Blob) {
      $('input[type=file].live_review').on('change', function (){
          var reader = new FileReader();
          var img = $('img[alt=ava]')[0];
          reader.readAsDataURL(this.files[0]);
          reader.onload = function (e) {
              img.src = e.target.result;
          }
      });
  }else{
      console.warn( "Ваш браузер не поддерживает FileAPI");
  }


  // Validate inputs of form
  $('input.form-control[pattern]').keyup(function(){
      var pr = $(this).closest('.form-group-sm,.form-group');
      pr.removeClass('has-success');
      pr.removeClass('has-error');
      pr.find('.form-control-feedback').remove();
      if($(this)[0].checkValidity()){
          pr.addClass('has-success');
          $(this).after('<span class="glyphicon glyphicon-ok form-control-feedback"></span>');
      }else{
          pr.addClass('has-error');
          $(this).after('<span class="glyphicon glyphicon-remove form-control-feedback"></span>');
      }

  });

});
