var noAlert = true;
var isOpen  = false;
var timeOut = 12000;
var tID     = '';
var formID  = '';
var shown   = [ ];
var dLong   = 'yyyy-M-d HH:mm:ss';
var dShort  = 'yyyy-M-d';

/* Events */
$('.edit_details').live('click', showEditUserForm);
$('.cancel_details').live('click', cancelForm);
$('.submit_details').live('click', submitFormDetails);
$('.delete_details').live('click', deleteFormDetails);
$('.show_selected').live('click', populateListForm);
$('.show_groups').live('click', showItems);
$('.remove_group').live('click', removeGroup);
$('.add_group').live('click', addGroup);


/* Binds */
$('body').keyup(cancelOverlay);
$(window).bind('resize',showOverlayBox);

$(document).ready(function() {
    clearMessage();
    initDatePickers();
});

var toggleContent = function(e) {
    if ($('#details_'+this.id).css('display') == 'none') {
        $('#details_'+this.id).slideDown(300);
    } else {
        $('#details_'+this.id).slideUp(300);
    }
    return false;
};


/* Init Functions */
function initDatePickers() {
    $('#userEffectiveStartDate, #userEffectiveEndDate').datepicker({
        dateFormat: 'yy-mm-dd',
        maxDate: '+10y',
        showButtonPanel: true,
        changeMonth: true,
        changeYear: true
    });
}


/* Overlay Functions */
function clearMessage(out) {
    if (!out) out = timeOut;
    tID = setTimeout(function(){ $('#message').html('') }, out);
}

function showOverlay(overlay) {
    if (tID) clearTimeout(tID);
    if (!overlay) overlay = 'overlay';
    $('#'+overlay).css('display', 'block');
    $('#'+overlay).height($(document).height());
    $('#message').css('color','#000000');
    $('#message').css('margin-left','10px');
    $('#message').css('font-weight','bold');
    $('#message').html('Loading...Please Wait!');
}

function showOverlayBox(overlay, layer) {
    //if box is not set to open then don't do anything
    if (isOpen == false) return;
    // set the properties of the overlay box, the left and top positions
    $(overlay).css({
        display: 'block',
        left: ($('#middle').width() - $(overlay).width())/2,
        top: $(window).scrollTop()+50,
        position: 'absolute'
    });
    // set the window background for the overlay. i.e the body becomes darker
    if (layer) {
        $('.background-cover-top').css({
            display: 'block',
            width: '100%',
            height: $(document).height()
        });
        $(overlay).css({ 'z-index': $(overlay).css('z-index')+layer });
    } else {
        $('.background-cover').css({
            display: 'block',
            width: '100%',
            height: $(document).height()
        });
    }
}

function hideOverlay(overlay, out) {
    if (!overlay) overlay = 'overlay';
    $('#'+overlay).css('display', 'none');
    clearMessage(out);
}

function doOverlayOpen(overlay, layer) {
    overlay = '#overlay-box-'+overlay;
    //set status to open
    isOpen = true;
    showOverlayBox(overlay, layer);
    if (layer) {
        $('.background-cover-top').css({opacity: 0}).animate({opacity: 0.5, backgroundColor: '#000'});
    } else {
        $('.background-cover').css({opacity: 0}).animate({opacity: 0.5, backgroundColor: '#000'});
    }
    // dont follow the link : so return false.
    return false;
}

function doOverlayClose(overlay, layer) {
    overlay = '#overlay-box-'+overlay;
    //set status to closed
    isOpen = false;
    $(overlay).css('display', 'none');
    // now animate the background to fade out to opacity 0
    // and then hide it after the animation is complete.
    if (layer) {
        $('.background-cover-top').animate( {opacity: 0}, 'fast', null, function() { $(this).hide(); } );
        $(overlay).css({ 'z-index': $(overlay).css('z-index')-layer });
    } else {
        $('.background-cover').animate( {opacity: 0}, 'fast', null, function() { $(this).hide(); } );
    }
}

function doOverlaySwap(close_overlay, open_overlay) {
    // close the current overlay
    overlay = '#overlay-box-'+close_overlay;
    //set status to closed
    isOpen = false;
    $(overlay).css('display', 'none');
    // open the next overlay
    overlay = '#overlay-box-'+open_overlay;
    //set status to open
    isOpen = true;
    showOverlayBox(overlay);
    return false;
}


/* Main Functions */
function cancelOverlay(e) {
    var keyCode;
    if (e == null) {
        keyCode = event.keyCode;
    } else { // mozilla
        keyCode = e.which;
    }
    if (keyCode == 27) {
        if (formID.match('-form')) {
            $('#'+formID+' .cancel_button').trigger('click');
        } else {
            $('#'+formID+'-form .cancel_button').trigger('click');
        }
        cancelForm(formID, formID);
        formID  = '';
    }
}

function cancelForm(event, id) {
    var thisId  = id ? id : this.id;
    var parts   = thisId.split('_');
    var display = parts[1];
    $('#'+display+'-form').find('input').each(function(){
        if ($('#'+this.id).attr('type') == 'text') {
            $('#'+this.id).attr('value', '');
        }
    });
    $('#'+display+'-form').find('select').each(function(){
        if (this.id.match('_group')) {
            $('#'+this.id).find('option').remove();
        }
    });
    doOverlayClose(display);
}

function submitFormDetails(event, id) {
    var thisId  = id ? id : this.id;
    var object  = thisId.replace('submit_', '');
    var action  = '/REST/admin';
    formID      = object
    if (validateForm(object, id)) {
        return false;
    }
    if (object == 'group') {
        $('#permission_group').children().each(function(){
            $(this).attr('selected', true);
        });
        $('#application_group').children().each(function(){
            $(this).attr('selected', true);
        });
    }
    if (object == 'user') {
        $('#user_group').children().each(function(){
            $(this).attr('selected', true);
        });
    }
    if ($('#'+object+'Id').val()) {
        action = action+'/edit/'+object+'/'+$('#'+object+'Id').val();
        $('#'+object+'Action').attr('value', 'updated');
    } else {
        action = action+'/create/'+object;
        $('#'+object+'Action').attr('value', 'created');
    }
    var params = $('#'+object+'-form').serialize();
    $.ajax(
        {
            url: action,
            type: 'post',
            dataType: 'json',
            data: params,
            timeout: 120000,
            error: failedEntryForm,
            success: updateEntryForm,
        }
    );
}

function addGroup(event) {
    var id  = this.id.replace('add_', '');
    var reg = new RegExp( '(\\w+)_group' );
    var got = id.match(reg);
    var ids = 'groups';
    if (got) {
        ids = got[1]+'_groups';
    }
    $('#'+ids+' option:selected').each(function(){
        var option = $(this)[0].cloneNode(true);
        var value  = $(option).val();
        if (!$('#'+id+' option[value="'+value+'"]').val()) {
            $(option).appendTo('#'+id);
        }
    });
}

function removeGroup(event) {
    var id  = this.id.replace('remove_', '');
    $('#'+id+' option:selected').remove();
}

function deleteFormDetails(event) {
    var thisId = id ? id : this.id;
    var parts  = thisId.split('_');
    var object = parts[0];
    var action = parts[1];
    var id     = parts[2];
    var confirmed = confirm('Are you sure you want to Delete this Entry?');
    if (confirmed == false) {
        doOverlayClose(object);
        return 1;
    }
    if (object == 'user') {
        id     = $('#'+action+'Id').val();
        object = action;
    }
    $.getJSON('/REST/admin/delete/'+object+'/'+id, updateEntryForm);
}

function failedEntryForm(data) {
    if (data['status'] == 500) data['message'] = data['status'] + ': ' + data['statusText'];
    updateStatus(data);
}

function updateEntryForm(data) {
    doOverlayClose(data['type']);
    updateStatus(data);
    if (data['status'] != 200) return;
    window.location.replace('/?limit='+$('#'+data['type']+'Limit').val());
}

function updateStatus(data) {
    if (tID) clearTimeout(tID);
    var status_msg = $('#message');
    if (data['status'] != 200) {
        status_msg.css('color','red');
    } else {
        status_msg.css('color','green');
    }
    status_msg.html(data['message']);
    clearMessage();
}

function showNewUserForm(event) {
    $('#title').html('Create');
    $('.edit-form').hide();
    $('.create-form').show();
    formID = 'user'
    doOverlayOpen(formID);
}

function showEditUserForm(event) {
    var parts   = this.id.split('_');
    var object  = parts[0];
    var id      = parts[1];
    formID      = object;
    $.getJSON('/REST/admin/view/'+object+'/'+id, populateUserForm);
    $('#title').html('Edit');
    $('.create-form').hide();
    $('.edit-form').show();
    doOverlayOpen(object);
}

function showApplicationForm(event) {
    $('.application-form').show();
    formID = 'application';
    $.getJSON('/REST/admin/get/'+formID, populateForm);
    doOverlayOpen(formID);
}

function showPermissionForm(event) {
    $('.permission-form').show();
    formID = 'permission';
    $.getJSON('/REST/admin/get/'+formID, populateForm);
    doOverlayOpen(formID);
}

function showGroupForm(event) {
    $('.group-form').show();
    formID = 'group';
    $.getJSON('/REST/admin/get/'+formID, populateForm);
    doOverlayOpen(formID);
}

function showItems(event, element, id) {
    var category = id ? id : this.id;
    var reg = new RegExp( '(show|close)_(\\w+_)*(\\w+)' );
    var got = category.match(reg);
    var ids = '_menu';
    if (got[3]) ids = got[3]+'_menu';
    if (got[2]) ids = got[2]+ids;
    $('#'+ids).toggle();
}

function showIndexPage(event) {
    window.location.href = '/';
}

function showReports(event) {
    window.location.href = '/reports';
}

function reloadPage() {
    window.location.reload();
}

function populateForm(data) {
    populateMenu(data['results'], data['type']);
}

function populateListForm(data) {
    var selected = $('#'+this.id+' option:selected');
    if (selected.val() == 0) {
        $('#'+this.id+'_id').hide();
        $('#'+this.id+'Id').attr('value', '');
        $('#'+this.id+'Name').attr('value', '');
        if (this.id == 'group') {
            $('#application_group').children().remove();
            $('#permission_group').children().remove();
        }
    } else {
        var values = selected.text().split('-');
        var id     = values.shift();
        var name   = values.join('-');
        $('#'+this.id+'_id').show();
        $('#'+this.id+'Id').attr('value', id);
        $('#'+this.id+'Name').attr('value', name);
        if (this.id == 'group') {
            $('#application_group').children().remove();
            $('#permission_group').children().remove();
            $.getJSON('/REST/admin/view/group/'+id, populateGroupAttrs);
        }
    }
}

function populateUserForm(data) {
    $('#userId').val(data['result']['id']);
    $('#userEffectiveStartDate').val(data['result']['effectiveStart']);
    $('#userEffectiveEndDate').val(data['result']['effectiveEnd']);
    $('#userUserName').val(data['result']['userName']);
    $('#userFirstName').val(data['result']['firstName']);
    $('#userLastName').val(data['result']['lastName']);
    $('#userEmailAddress').val(data['result']['emailAddress']);
    $('#userActionType').val(data['result']['actionType']);
    $('#userUpdatedDate').val(data['result']['updatedDate']);
    $('#userCreatedDate').val(data['result']['createdDate']);
    $('#userUpdatedBy').val(data['result']['updatedBy']);
    if (data['result'] && data['result']['group']) {
        populateMenu(data['result']['group'], 'user_group')
    }
}

function populateMenu(data, type) {
    if (!data.length) return;
    if (!type) type = '';
    $('#'+type).find('option').remove();
    if (data) {
        if (!type.match('_group')) {
            var option = new Option('New '+type.charAt(0).toUpperCase()+type.substr(1), 0);
            $('#'+type).append(option);
        }
        for (var i = 0; i < data.length; i++) {
            var option = new Option(data[i]['label'], data[i]['id']);
            $('#'+type).append(option);
        }
    }
}

function populateGroupAttrs(data) {
    if (data) {
        populateMenu(data['result']['permissions'], 'permission_group')
        populateMenu(data['result']['applications'], 'application_group')
    }
}

function validateForm(object, id) {
    var required = new Array('Name');
    var title    = 'Entry Info ';
    var error    = false;
    if (object == 'user') {
        required = new Array('UserName', 'FirstName', 'LastName', 'EmailAddress', 'EffectiveStartDate', 'EffectiveEndDate');
    }
    for (key in required) {
        var field = required[key].replace(/ /g, '');
        var value = $('#'+object+field).val();
        if (!value) {
            $('#user'+field+'Label').css('color', '#FF0000');
            message = {
                'status': 404,
                'message': title +required[key]+' is Required'
            };
            updateStatus(message);
            error = true;
        } else {
            $('#user'+field+'Label').css('color', '#000000');
        }
    }
    return error;
}

function approveRelease(event) {
    doOverlayOpen('loading');
    $.getJSON('/REST/release/approve/'+$('#releaseId').val(), updateApproveStatus);
}

function approveReleaseList(event, id) {
    var itemId = id ? id : this.id;
    var parts  = itemId.split('_');
    var releaseId = parts[1];
    doOverlayOpen('loading');
    $.getJSON('/REST/release/approve/'+releaseId, updateApproveStatusList);
}

function getProjects(event, id) {
    var itemId = id ? id : this.id;
    var selected = $('#'+itemId+' option:selected');
    doOverlayOpen('loading');
    $.getJSON('/REST/release/projects', updateProjectList);
}

function getEnvironments(event, id) {
    var selected = $('#releaseProject option:selected');
    doOverlayOpen('loading');
    $.getJSON('/REST/release/environments/'+selected.val(), updateEnvironmentList);
}

function getBuilds(event, id) {
    var itemId = id ? id : this.id;
    var selected = $('#'+itemId+' option:selected');
    doOverlayOpen('loading');
    $.getJSON('/REST/release/builds/'+selected.val(), updateBuildList);
}
