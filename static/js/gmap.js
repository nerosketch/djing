function toggleCategory(category) {
    $.each(gmap_markers, function (key, marker) {
        if (marker.category == category) {
            if (marker.getVisible() == true) {
                marker.setVisible(false)
            } else {
                marker.setVisible(true)
            }
        }
    })
}

function toggleTag(tag) {
    $.each(gmap_markers, function (key, marker) {
        $.each(marker.tags, function (key, this_tag) {
            if (this_tag == tag) {
                if (marker.getVisible() == true) {
                    marker.setVisible(false)
                } else {
                    marker.setVisible(true)
                }
            }
        })
    })
}

$(document).ready(function () {

    var myLatlng = new Array();
    var open_marker = '';

    myLatlng[0] = new google.maps.LatLng(28.5000, -81.4500);

    var map = new google.maps.Map(document.getElementById("gmap_canvas"), {
        zoom: 1,
        center: myLatlng[0],
        mapTypeId: google.maps.MapTypeId.ROADMAP
    });

    $.getJSON('/map/markers.json', function (data) {
        var categories = new Array();
        var tags = new Array();
        var infowindow = new google.maps.InfoWindow({content: ''})
        gmap_markers = []
        $.each(data, function (key, item) {
            var content = '<span class="name">' + item.fields.name + '</span><br/><span class="phone">' + item.fields.phone + '</span><br/><span class="email">' + item.fields.email + '</span><br/><span class="url">' + item.fields.url + '</span><br/>'
            var latLng = new google.maps.LatLng(item.fields.latitude, item.fields.longitude)
            var marker = new google.maps.Marker({
                position: latLng,
                map: map,
                title: item.fields.name,
                category: item.fields.category,
                tags: item.fields.sub_categories,
            })
            google.maps.event.addListener(marker, "click", function () {
                infowindow.content = content
                infowindow.open(map, marker);
            });
            gmap_markers.push(marker)

            if ($.inArray(item.fields.category, categories) == -1) {
                categories.push(item.fields.category)
            }
            $.each(item.fields.sub_categories, function (key, item) {
                if ($.inArray(item, tags) == -1) {
                    tags.push(item)
                }
            })
        })
        $.each(categories, function (key, category) {
            var $button = $(' <a href="#category_' + category + '">' + category + '</a> ').bind('click', function () {
                toggleCategory(category)
            })
            $('#gmap_categories').append($button)
        })

        $.each(tags, function (key, tag) {
            var $button = $(' <a href="#tag_' + tag + '">' + tag + '</a> ').bind('click', function () {
                toggleTag(tag)
            })
            $('#gmap_sub_categories').append($button)
        })
    })
    google.maps.event.addListener(map, 'click', function () {
        if (open_marker != '') {
            open_marker.close();
        }
        open_marker = '';
    });

})
