/**
 * jQuery Form Plugin
 * version: 2.37 (13-FEB-2010)
 * @requires jQuery v1.3.2 or later
 *
 * Examples and documentation at: http://malsup.com/jquery/form/
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 */
;(function($){$.fn.ajaxSubmit=function(options){if(!this.length){log('ajaxSubmit: skipping submit process - no element selected');return this;}if(typeof options=='function')options={success:options};var url=$.trim(this.attr('action'));if(url){url=(url.match(/^([^#]+)/)||[])[1];}url=url||window.location.href||'';options=$.extend({url:url,type:this.attr('method')||'GET',iframeSrc:/^https/i.test(window.location.href||'')?'javascript:false':'about:blank'},options||{});var veto={};this.trigger('form-pre-serialize',[this,options,veto]);if(veto.veto){log('ajaxSubmit: submit vetoed via form-pre-serialize trigger');return this;}if(options.beforeSerialize&&options.beforeSerialize(this,options)===false){log('ajaxSubmit: submit aborted via beforeSerialize callback');return this;}var a=this.formToArray(options.semantic);if(options.data){options.extraData=options.data;for(var n in options.data){if(options.data[n]instanceof Array){for(var k in options.data[n])a.push({name:n,value:options.data[n][k]});}else
a.push({name:n,value:options.data[n]});}}if(options.beforeSubmit&&options.beforeSubmit(a,this,options)===false){log('ajaxSubmit: submit aborted via beforeSubmit callback');return this;}this.trigger('form-submit-validate',[a,this,options,veto]);if(veto.veto){log('ajaxSubmit: submit vetoed via form-submit-validate trigger');return this;}var q=$.param(a);if(options.type.toUpperCase()=='GET'){options.url+=(options.url.indexOf('?')>=0?'&':'?')+q;options.data=null;}else
options.data=q;var $form=this,callbacks=[];if(options.resetForm)callbacks.push(function(){$form.resetForm();});if(options.clearForm)callbacks.push(function(){$form.clearForm();});if(!options.dataType&&options.target){var oldSuccess=options.success||function(){};callbacks.push(function(data){$(options.target).html(data).each(oldSuccess,arguments);});}else if(options.success)callbacks.push(options.success);options.success=function(data,status,xhr){for(var i=0,max=callbacks.length;i<max;i++)callbacks[i].apply(options,[data,status,xhr||$form,$form]);};var files=$('input:file',this).fieldValue();var found=false;for(var j=0;j<files.length;j++)if(files[j])found=true;var multipart=false;if((files.length&&options.iframe!==false)||options.iframe||found||multipart){if(options.closeKeepAlive)$.get(options.closeKeepAlive,fileUpload);else
fileUpload();}else
$.ajax(options);this.trigger('form-submit-notify',[this,options]);return this;function fileUpload(){var form=$form[0];if($(':input[name=submit]',form).length){alert('Error: Form elements must not be named "submit".');return;}var opts=$.extend({},$.ajaxSettings,options);var s=$.extend(true,{},$.extend(true,{},$.ajaxSettings),opts);var id='jqFormIO'+(new Date().getTime());var $io=$('<iframe id="'+id+'" name="'+id+'" src="'+opts.iframeSrc+'" />');var io=$io[0];$io.css({position:'absolute',top:'-1000px',left:'-1000px'});var xhr={aborted:0,responseText:null,responseXML:null,status:0,statusText:'n/a',getAllResponseHeaders:function(){},getResponseHeader:function(){},setRequestHeader:function(){},abort:function(){this.aborted=1;$io.attr('src',opts.iframeSrc);}};var g=opts.global;if(g&&!$.active++)$.event.trigger("ajaxStart");if(g)$.event.trigger("ajaxSend",[xhr,opts]);if(s.beforeSend&&s.beforeSend(xhr,s)===false){s.global&&$.active--;return;}if(xhr.aborted)return;var cbInvoked=0;var timedOut=0;var sub=form.clk;if(sub){var n=sub.name;if(n&&!sub.disabled){options.extraData=options.extraData||{};options.extraData[n]=sub.value;if(sub.type=="image"){options.extraData[name+'.x']=form.clk_x;options.extraData[name+'.y']=form.clk_y;}}}setTimeout(function(){var t=$form.attr('target'),a=$form.attr('action');form.setAttribute('target',id);if(form.getAttribute('method')!='POST')form.setAttribute('method','POST');if(form.getAttribute('action')!=opts.url)form.setAttribute('action',opts.url);if(!options.skipEncodingOverride){$form.attr({encoding:'multipart/form-data',enctype:'multipart/form-data'});}if(opts.timeout)setTimeout(function(){timedOut=true;cb();},opts.timeout);var extraInputs=[];try{if(options.extraData)for(var n in options.extraData)extraInputs.push($('<input type="hidden" name="'+n+'" value="'+options.extraData[n]+'" />').appendTo(form)[0]);$io.appendTo('body');io.attachEvent?io.attachEvent('onload',cb):io.addEventListener('load',cb,false);form.submit();}finally{form.setAttribute('action',a);t?form.setAttribute('target',t):$form.removeAttr('target');$(extraInputs).remove();}},10);var domCheckCount=50;function cb(){if(cbInvoked++)return;io.detachEvent?io.detachEvent('onload',cb):io.removeEventListener('load',cb,false);var ok=true;try{if(timedOut)throw'timeout';var data,doc;doc=io.contentWindow?io.contentWindow.document:io.contentDocument?io.contentDocument:io.document;var isXml=opts.dataType=='xml'||doc.XMLDocument||$.isXMLDoc(doc);log('isXml='+isXml);if(!isXml&&(doc.body==null||doc.body.innerHTML=='')){if(--domCheckCount){cbInvoked=0;setTimeout(cb,100);return;}log('Could not access iframe DOM after 50 tries.');return;}xhr.responseText=doc.body?doc.body.innerHTML:null;xhr.responseXML=doc.XMLDocument?doc.XMLDocument:doc;xhr.getResponseHeader=function(header){var headers={'content-type':opts.dataType};return headers[header];};if(opts.dataType=='json'||opts.dataType=='script'){var ta=doc.getElementsByTagName('textarea')[0];if(ta)xhr.responseText=ta.value;else{var pre=doc.getElementsByTagName('pre')[0];if(pre)xhr.responseText=pre.innerHTML;}}else if(opts.dataType=='xml'&&!xhr.responseXML&&xhr.responseText!=null){xhr.responseXML=toXml(xhr.responseText);}data=$.httpData(xhr,opts.dataType);}catch(e){ok=false;$.handleError(opts,xhr,'error',e);}if(ok){opts.success(data,'success');if(g)$.event.trigger("ajaxSuccess",[xhr,opts]);}if(g)$.event.trigger("ajaxComplete",[xhr,opts]);if(g&&!--$.active)$.event.trigger("ajaxStop");if(opts.complete)opts.complete(xhr,ok?'success':'error');setTimeout(function(){$io.remove();xhr.responseXML=null;},100);};function toXml(s,doc){if(window.ActiveXObject){doc=new ActiveXObject('Microsoft.XMLDOM');doc.async='false';doc.loadXML(s);}else
doc=(new DOMParser()).parseFromString(s,'text/xml');return(doc&&doc.documentElement&&doc.documentElement.tagName!='parsererror')?doc:null;};};};$.fn.ajaxForm=function(options){return this.ajaxFormUnbind().bind('submit.form-plugin',function(){$(this).ajaxSubmit(options);return false;}).bind('click.form-plugin',function(e){var target=e.target;var $el=$(target);if(!($el.is(":submit,input:image"))){var t=$el.closest(':submit');if(t.length==0)return;target=t[0];}var form=this;form.clk=target;if(target.type=='image'){if(e.offsetX!=undefined){form.clk_x=e.offsetX;form.clk_y=e.offsetY;}else if(typeof $.fn.offset=='function'){var offset=$el.offset();form.clk_x=e.pageX-offset.left;form.clk_y=e.pageY-offset.top;}else{form.clk_x=e.pageX-target.offsetLeft;form.clk_y=e.pageY-target.offsetTop;}}setTimeout(function(){form.clk=form.clk_x=form.clk_y=null;},100);});};$.fn.ajaxFormUnbind=function(){return this.unbind('submit.form-plugin click.form-plugin');};$.fn.formToArray=function(semantic){var a=[];if(this.length==0)return a;var form=this[0];var els=semantic?form.getElementsByTagName('*'):form.elements;if(!els)return a;for(var i=0,max=els.length;i<max;i++){var el=els[i];var n=el.name;if(!n)continue;if(semantic&&form.clk&&el.type=="image"){if(!el.disabled&&form.clk==el){a.push({name:n,value:$(el).val()});a.push({name:n+'.x',value:form.clk_x},{name:n+'.y',value:form.clk_y});}continue;}var v=$.fieldValue(el,true);if(v&&v.constructor==Array){for(var j=0,jmax=v.length;j<jmax;j++)a.push({name:n,value:v[j]});}else if(v!==null&&typeof v!='undefined')a.push({name:n,value:v});}if(!semantic&&form.clk){var $input=$(form.clk),input=$input[0],n=input.name;if(n&&!input.disabled&&input.type=='image'){a.push({name:n,value:$input.val()});a.push({name:n+'.x',value:form.clk_x},{name:n+'.y',value:form.clk_y});}}return a;};$.fn.formSerialize=function(semantic){return $.param(this.formToArray(semantic));};$.fn.fieldSerialize=function(successful){var a=[];this.each(function(){var n=this.name;if(!n)return;var v=$.fieldValue(this,successful);if(v&&v.constructor==Array){for(var i=0,max=v.length;i<max;i++)a.push({name:n,value:v[i]});}else if(v!==null&&typeof v!='undefined')a.push({name:this.name,value:v});});return $.param(a);};$.fn.fieldValue=function(successful){for(var val=[],i=0,max=this.length;i<max;i++){var el=this[i];var v=$.fieldValue(el,successful);if(v===null||typeof v=='undefined'||(v.constructor==Array&&!v.length))continue;v.constructor==Array?$.merge(val,v):val.push(v);}return val;};$.fieldValue=function(el,successful){var n=el.name,t=el.type,tag=el.tagName.toLowerCase();if(typeof successful=='undefined')successful=true;if(successful&&(!n||el.disabled||t=='reset'||t=='button'||(t=='checkbox'||t=='radio')&&!el.checked||(t=='submit'||t=='image')&&el.form&&el.form.clk!=el||tag=='select'&&el.selectedIndex==-1))return null;if(tag=='select'){var index=el.selectedIndex;if(index<0)return null;var a=[],ops=el.options;var one=(t=='select-one');var max=(one?index+1:ops.length);for(var i=(one?index:0);i<max;i++){var op=ops[i];if(op.selected){var v=op.value;if(!v)v=(op.attributes&&op.attributes['value']&&!(op.attributes['value'].specified))?op.text:op.value;if(one)return v;a.push(v);}}return a;}return el.value;};$.fn.clearForm=function(){return this.each(function(){$('input,select,textarea',this).clearFields();});};$.fn.clearFields=$.fn.clearInputs=function(){return this.each(function(){var t=this.type,tag=this.tagName.toLowerCase();if(t=='text'||t=='password'||tag=='textarea')this.value='';else if(t=='checkbox'||t=='radio')this.checked=false;else if(tag=='select')this.selectedIndex=-1;});};$.fn.resetForm=function(){return this.each(function(){if(typeof this.reset=='function'||(typeof this.reset=='object'&&!this.reset.nodeType))this.reset();});};$.fn.enable=function(b){if(b==undefined)b=true;return this.each(function(){this.disabled=!b;});};$.fn.selected=function(select){if(select==undefined)select=true;return this.each(function(){var t=this.type;if(t=='checkbox'||t=='radio')this.checked=select;else if(this.tagName.toLowerCase()=='option'){var $sel=$(this).parent('select');if(select&&$sel[0]&&$sel[0].type=='select-one'){$sel.find('option').selected(false);}this.selected=select;}});};function log(){if($.fn.ajaxSubmit.debug&&window.console&&window.console.log)window.console.log('[jquery.form] '+Array.prototype.join.call(arguments,''));};})(jQuery);

/**
 * jCarouselLite - jQuery plugin to navigate images/any content in a carousel style widget.
 *
 * http://gmarwaha.com/jquery/jcarousellite/
 *
 * Copyright (c) 2007 Ganeshji Marwaha (gmarwaha.com)
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 * Version: 1.0.1
 */
(function($){$.fn.jCarouselLite=function(o){o=$.extend({btnPrev:null,btnNext:null,btnGo:null,mouseWheel:false,auto:null,speed:200,easing:null,vertical:false,circular:true,visible:3,start:0,scroll:1,beforeStart:null,afterEnd:null},o||{});return this.each(function(){var b=false,animCss=o.vertical?"top":"left",sizeCss=o.vertical?"height":"width";var c=$(this),ul=$("ul",c),tLi=$("li",ul),tl=tLi.size(),v=o.visible;if(o.circular){ul.prepend(tLi.slice(tl-v-1+1).clone()).append(tLi.slice(0,v).clone());o.start+=v}var f=$("li",ul),itemLength=f.size(),curr=o.start;c.css("visibility","visible");f.css({overflow:"hidden",float:o.vertical?"none":"left"});ul.css({margin:"0",padding:"0",position:"relative","list-style-type":"none","z-index":"1"});c.css({overflow:"hidden",position:"relative","z-index":"2",left:"0px"});var g=o.vertical?height(f):width(f);var h=g*itemLength;var j=g*v;f.css({width:f.width(),height:f.height()});ul.css(sizeCss,h+"px").css(animCss,-(curr*g));c.css(sizeCss,j+"px");if(o.btnPrev)$(o.btnPrev).click(function(){return go(curr-o.scroll)});if(o.btnNext)$(o.btnNext).click(function(){return go(curr+o.scroll)});if(o.btnGo)$.each(o.btnGo,function(i,a){$(a).click(function(){return go(o.circular?o.visible+i:i)})});if(o.mouseWheel&&c.mousewheel)c.mousewheel(function(e,d){return d>0?go(curr-o.scroll):go(curr+o.scroll)});if(o.auto)setInterval(function(){go(curr+o.scroll)},o.auto+o.speed);function vis(){return f.slice(curr).slice(0,v)};function go(a){if(!b){if(o.beforeStart)o.beforeStart.call(this,vis());if(o.circular){if(a<=o.start-v-1){ul.css(animCss,-((itemLength-(v*2))*g)+"px");curr=a==o.start-v-1?itemLength-(v*2)-1:itemLength-(v*2)-o.scroll}else if(a>=itemLength-v+1){ul.css(animCss,-((v)*g)+"px");curr=a==itemLength-v+1?v+1:v+o.scroll}else curr=a}else{if(a<0||a>itemLength-v)return;else curr=a}b=true;ul.animate(animCss=="left"?{left:-(curr*g)}:{top:-(curr*g)},o.speed,o.easing,function(){if(o.afterEnd)o.afterEnd.call(this,vis());b=false});if(!o.circular){$(o.btnPrev+","+o.btnNext).removeClass("disabled");$((curr-o.scroll<0&&o.btnPrev)||(curr+o.scroll>itemLength-v&&o.btnNext)||[]).addClass("disabled")}}return false}})};function css(a,b){return parseInt($.css(a[0],b))||0};function width(a){return a[0].offsetWidth+css(a,'marginLeft')+css(a,'marginRight')};function height(a){return a[0].offsetHeight+css(a,'marginTop')+css(a,'marginBottom')}})(jQuery);

/**
 * BmoreFiber JS
 */
var baltimore = new google.maps.LatLng(39.31, -76.68);
var bounding = new google.maps.LatLngBounds(new google.maps.LatLng(39.2429, -76.6942), new google.maps.LatLng(39.4298, -76.4566));
var infoWindow = new google.maps.InfoWindow();
var markerBounds = new google.maps.LatLngBounds();
var markerArray = [];
var apiResponseArray = [];
var timeout = null;
var map = null;
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
    map = new google.maps.Map(document.getElementById("supporter_map"), {
        zoom: 11,
        center: baltimore,
        mapTypeId: google.maps.MapTypeId.TERRAIN,
        mapTypeControl: false,
        scrollwheel: false,
        navigationControlOptions: {
            position: google.maps.ControlPosition.TOP_RIGHT
        }
    });
    // Setup map click event to close any open info windows
    google.maps.event.addListener(map, "click", function(){
        infoWindow.close();
    });
    
    // set the timout to begin downloading and plotting the pushpins
    timeout = window.setTimeout(displayPushPins, 100);

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

    // Setup the Keyword filters
    $("#cloud").accordion({ collapsible: true, autoHeight: false });
    $(".word_button").click(function(){
        // Fire the map's click event to close any open infowindows
        infoWindow.close();
        
        // If the button has the word-selected class, we're toggling it off, so show all the markers again
        if($(this).hasClass("word-selected")){
            $(this).removeClass("word-selected");
            displayPushPins();
        } else {
            $(".word_button").removeClass("word-selected");
            $(this).addClass("word-selected");
            displayPushPins({ word: $(this).attr("name")});
        }
    });
    
}); // Close of .ready() block


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

function removeMarkers(){
    while (marker = markerArray.pop()){
        marker.setMap(null);
    }
}

// initial call from $(document).ready()), initiates the API call and add the pushpins
function displayPushPins(options) 
{   
    default_params = { limit: "1000", appid: "bmorefiber", markers: "true" };
    
    // Show a spinner
    $("#map_spinner").show();
    
    // Kill any timeouts that might be in progress
    clearTimeout(timeout);
    
    // remove any existing map markers
    removeMarkers();
    
    // Make our query
    $.ajax({ url: "/api/supporters",
        dataType: 'json',
        data: $.extend(default_params, options),
        success: function (data) {
            apiResponseArray = data.data;
            // if we have markers, make the calls to add them to map
            if (apiResponseArray.length > 0) {
                window.setTimeout(addMarkersToMapAsync, 100);
            }
        }
    });
}
// called on timeout to add markers in batches
function addMarkersToMapAsync() {
    var iconTemplate = "/static/images/markers/marker{num}.png";
    // loop through return array, pop off 50 at a time
    for (var i = 0; i < 50; i++) {

        // grab the marker details
        var marker = apiResponseArray.pop();
        var count = parseInt(marker.count, 10);
        var content = buildContent(marker, count); 
        // call the make marker method on the map
        makeMarker({
            position: parseGeoLoc(marker.location),
            content: content,
            title: (count > 1) ? count + " supporters" : "1 supporter",
            icon: (count > 1 && count < 100) ? iconTemplate.replace("{num}", count) : iconTemplate.replace("{num}", "")
        });

        // if no more items, exit
        if (apiResponseArray.length == 0) {
            // hide a spinner
            $("#map_spinner").hide();
            break;
        }
    }
    // stop the callback when the apiResponse array is empty
    if (apiResponseArray.length > 0) {
        timeout = window.setTimeout(addMarkersToMapAsync, 200);
    }
}
// helper method to build content based on list of supporters for a marker
function buildContent(marker, count) {

    // use an array to avoid string concat for speed.  most will be fine, but one pushpin has count = 84, another at 56, etc.
    var content = [];
    var message_templ = "<div class='infowindow'><h3>message</h3><p><i>name, date</i></p></div>";
    for (var j = 0; j < count; j++) 
    {
        // grab the person and add their details
        var person = marker.supporters[j];
        content.push(message_templ.replace("message", person.reason).replace("name", person.name).replace("date", person.date));
    }
    return content.join("\n");
}
// parse the geoloc into google obj
function parseGeoLoc(s) {
    var pts = new String(s).split(",");
    return new google.maps.LatLng(parseFloat(pts[0]), parseFloat(pts[1]));
}


function loadVideo(player_url, target_div) {
    swfobject.embedSWF(
        player_url + '&rel=0&border=0&fs=1&autoplay=1', 
        target_div, '330', '248', '9.0.0', false, 
        false, {allowfullscreen: 'false'});
}

function renderVideos(data) {
    var pages = 1;
    var content = ['<li>'];
    var div_tpl = "<div class='video'><a id='video_{{i}}' href='{{url}}' title='{{title}}'><img src='{{src}}' alt='{{alt}}' width='330' height='248'/></a></div>";
    var feed = data.feed;
    var entries = feed.entry || [];
    for (var i = 0; i < entries.length; i++) {
        if(i > 0 && i % 6 == 0){
            pages++;
            content.push("</li><li>");
        }
        var title = entries[i].title.$t;
        var src = entries[i].media$group.media$thumbnail[3].url;
        var url = entries[i].media$group.media$content[0].url;
        content.push(div_tpl.replace("{{src}}", src).replace("{{alt}}", title).replace("{{title}}", title).replace("{{i}}", i).replace("{{url}}", url));
    }
    content.push("</li>");
    $("#video_carousel ul").append(content.join("\n"));
    
    // Make direct links to the pages
    selectors = [];
    for (var i=1; i <= pages; i++) {
        selectors.push("#page_" + i);
        $(".carousel_pages").append("<button id='page_" + i + "'>" + i + "</button> ");
    };
    
    // Load YouTube videos when images are clicked
    $(".video a").click(function(){
        loadVideo(this.href, this.id);
        return false;
    });
    
    // Make a carousel
    $("#video_carousel").jCarouselLite({
        btnNext: ".next",
        btnPrev: ".prev",
        btnGo: selectors,
        visible: 1,
        circular: false
    });
}
  
// Google Analytics Tracking
(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    (document.getElementsByTagName('head')[0] || document.getElementsByTagName('body')[0]).appendChild(ga);
})();