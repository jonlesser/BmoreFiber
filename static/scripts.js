baltimore = new google.maps.LatLng(39.31, -76.61);
bounding = new google.maps.LatLngBounds(new google.maps.LatLng(39.2429, -76.6942), new google.maps.LatLng(39.4298, -76.4566));
$(document).ready(function() {
    jQuery.validator.setDefaults({ success: "valid", onkeyup: function(element){}, errorClass: "inputError"});
    jQuery.validator.addMethod("youtube", function(value, element) { 
        return this.optional(element) || /^http:\/\/www\.youtube\.com\/watch\?.*/.test(value); 
    }, "You need to use a YouTube video URL with in the form of http://www.youtube.com/watch?v=xxxxxxxxxxx");
    jQuery.validator.addMethod("valid_address", function(value, element) { 
        return ($("#id_geolat").val() == "") ?  false : true;
    }, "We couldn't locate that location.");

    // Setup Add your Voice form and dialog
    $("#id_address").live("blur", function(){
        var geocoder = new google.maps.Geocoder();
        geocoder.geocode({ address: $("#id_address").val(), bounds: bounding }, function(results, status) {
            if (status == google.maps.GeocoderStatus.ZERO_RESULTS || $("#id_address").val() == "") {
                $("#id_geolat").val("");
                $("#id_geolng").val("");
                $("#add_voice_form_map").empty().hide();
                $("#add_voice_form").validate().element("#id_geolng");
                return;
            }
            if (status != google.maps.GeocoderStatus.OK) {
                alert("Oh Noes, Google's geocoder service is down. Try again?");
                return;
            }
            
            // Make a new map with the location and append it after the field
            $("#add_voice_form_map").show();
            var add_map = new google.maps.Map(document.getElementById("add_voice_form_map"), {
                zoom: 13,
                center: results[0].geometry.location,
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                mapTypeControl: false,
                navigationControl: true,
                navigationControlOptions: {style: google.maps.NavigationControlStyle.SMALL },
                scaleControl: false,
                keyboardShortcuts: false,
                scrollwheel: false
            });
            var marker = new google.maps.Marker({
                map: add_map, 
                position: results[0].geometry.location
            });
            $("#id_geolat").val(results[0].geometry.location.lat());
            $("#id_geolng").val(results[0].geometry.location.lng());
            
            // Revalidate the address field to clear any errors that might be there
            $("#add_voice_form").validate().element("#id_geolng");
        });
    });
    $("#add_voice_form").validate({
        rules: {
            name:      { required: true },
            email:     { required: true, email: true },
            reason:    { required: true },
            address:   { required: true },
            geolng:    { valid_address: true },
            website:   { url: true },
            video_url: { url: true, youtube: true }
        }
    });
    $('#add_voice_form').ajaxForm({
        success: function(responseText){
            $("#add_voice_dialog").dialog("close");
            $("#success_dialog").dialog("open");
        }
    });
    $("#add_voice_dialog").dialog({
        title: 'Add your Voice', modal: true, resizable: false, draggable: false, autoOpen: false, 
        width: 283,
        height: 490,
        buttons: { 
            "Add your Voice": function() {
                // $('#add_voice_dialog').next().find("button").attr("disabled", "disabled").addClass("ui-state-disable");
                $('#add_voice_form').submit();
            }
        }
    });
    $("#add_voice_button").click(function(){$('#add_voice_dialog').dialog('open')});
    $(".add_voice_link").click(function(){$('#add_voice_dialog').dialog('open'); return false;});
    
    // Setup buttons
    $("button").addClass("ui-button ui-state-default ui-corner-all");
    $("button").hover(function(){
        $(this).addClass("ui-state-hover");
    }, function(){
        $(this).removeClass("ui-state-hover");
    });
    
    
    // Setup Add your Organization form and dialog
    $("#add_org_dialog").dialog({
        title: 'Add your Organization', modal: true, resizable: false, draggable: false, autoOpen: false, 
        width: 283,
        height: 330,
        buttons: { 
            "Add your Organization": function() {
                $('#add_org_form').submit(); 
            }
        }
    });
    $("#add_org_button").click(function(){$('#add_org_dialog').dialog('open')});
    $(".add_org_link").click(function(){$('#add_org_dialog').dialog('open'); return false;});
    $("#add_org_form").validate({
        rules: {
            name:      { required: true },
            email:     { required: true, email: true },
            reason:    {  },
            website:   { url: true }
        }
    });
    $('#add_org_form').ajaxForm({
        success: function(responseText){
            $("#add_org_dialog").dialog("close");
            $("#success_dialog").dialog("open");
        }
    });
    
    $("#success_dialog").dialog({
        title: 'Success', modal: true, resizable: false, draggable: false, autoOpen: false, 
        width: 283,
        height: 250,
        buttons: { 
            "I already did": function() {
                $("#success_dialog").dialog("close");
            },
            "Nominate Baltimore!": function() {
                window.location = "http://www.google.com/appserve/fiberrfi/public/options";
            }
        }
    });
    
    // Setup supporter map
    var map = new google.maps.Map(document.getElementById("supporter_map"), {
        zoom: 11,
        center: baltimore,
        mapTypeId: google.maps.MapTypeId.TERRAIN,
        mapTypeControl: false,
        scrollwheel: false,
        navigationControlOptions: {
            position: google.maps.ControlPosition.TOP_RIGHT
        },
    });
    // Add map markers
    var infoWindow = new google.maps.InfoWindow();
    var markerBounds = new google.maps.LatLngBounds();
    var markerArray = [];

    function makeMarker(options){
        var pushPin = new google.maps.Marker({map:map});
        pushPin.setOptions(options);
        google.maps.event.addListener(pushPin, "click", function(){
            infoWindow.setOptions(options);
            infoWindow.open(map, pushPin);
        });
        markerBounds.extend(options.position);
        markerArray.push(pushPin);
        return pushPin;
    }
    google.maps.event.addListener(map, "click", function(){
        infoWindow.close();
    });
    {% for marker in markers.items %}
        content = "<div class='infowindow'>";
        {% for user in marker.1.data %}
            content += "<h3>{{user.reason}}</h3>";
            content += "<p><i>{{user.name}}, {{user.date|date:"N j, Y"}}</i></p>";
        {% endfor %}
        content += "</div>";
        makeMarker({
            position: new google.maps.LatLng({{marker.0}}),
            content: content,
            {% ifequal marker.1.total 1 %}
                title: "{{marker.1.total}} supporter",
            {% else %}
                title: "{{marker.1.total}} supporters",
            {% endifequal %}
            {% if marker.1.lots %}
                icon: "/static/images/markers/blank.png"
            {% else %}
                {% ifequal marker.1.total 1 %}
                    icon: "/static/images/markers/marker.png"
                {% else %}
                    icon: "/static/images/markers/marker{{marker.1.total}}.png"
                {% endifequal %}
            {% endif %}
        });
    {% endfor %}

    // Setup YouTube Direct
    $("#youtube_direct_dialog").dialog({
        title: 'Submit a Video', modal: true, resizable: true, draggable: true, autoOpen: false, 
        width: 330,
        height: 540,
        beforeclose: function(event, ui) {
            $("#youtube_direct_link").show();
            $("#youtube_direct_button").show();
        }
    });
    $("#youtube_direct_link").click(function(){
        $("#youtube_direct_dialog").dialog("open");
        return false;
    });
    $("#youtube_direct_button").click(function(){
        $("#youtube_direct_dialog").dialog("open");
        return false;
    });
    var ytd = new Ytd();
    ytd.setAssignmentId("7");
    ytd.setCallToAction("youtube_direct_link");
    ytd.setCallToAction("youtube_direct_button");
    var containerWidth = 300;
    var containerHeight = 470;
    ytd.setYtdContainer("ytdContainer", containerWidth, containerHeight);
    ytd.ready();

    // If we're returning from ytd login, show the popup
    if (location.hash.search(/return\-sessionId/) > 0){
        $("#youtube_direct_dialog").dialog("open");
        location.hash = "";
    }

    // Setup the Keyword closer
    // $("#cloud").accordion({ collapsible: true, autoHeight: false });

});    
// Google Analytics Tracking
(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(ga);
})();