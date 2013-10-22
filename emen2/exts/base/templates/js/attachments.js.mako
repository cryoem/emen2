(function($) {
    $.widget("emen2.DownloadControl", {
        options: {
        },
        
        _create: function() {
            var self = this;
            $('.e2-download-allbids', this.element).click(function() {
                var s = $(this).attr('checked');
                if (!s) {s=false}
                $('input[name=bids]', this.element).each(function() {
                    $(this).attr('checked', s);
                });
                self.updatefilesize();
            });
    
            $('input[name=bids]', this.element).click(function() {
                self.updatefilesize();
            });
            this.updatefilesizes();
            this.updatefilesize();
        },
        
        updatefilesizes: function() {
            var c = $('.e2-download-filesizes', this.element);
            c.each(function() {
                var z = parseInt($(this).attr('data-filesize'));
                $(this).text(emen2.template.prettybytes(z));
            });
        },
        
        updatefilesize: function() {
            var s = 0;
            var c = $('input[name=bids]:checked', this.element);
            c.each(function() {
                var z = parseInt($(this).attr('data-filesize'));
                if (z > 0) {
                    s += z;
                }
            });
            $('.e2-download-filesize', this.element).text(emen2.template.prettybytes(s));
            $('.e2-download-filecount', this.element).text(c.length);
        },
    });
    
    $.widget("emen2.UploadControl", {
        options: {
            modal: true,
            action: '/upload/',
            redirect: '/',
            wait: 1000,
            param: 'file_binary',
        },
                
        _create: function() {
            var self = this;
            this.built = 0;
            this.files = [];            
            this.options.action = this.element.attr('action');
            this.options.redirect = $('input[name=_redirect]', this.element).val() || '';
            
            // Check that we have browser support for File API
            if (window.File && window.FileReader && window.FileList && window.Blob) {
                // Great success! All the File APIs are supported.
            } else {
                // alert('The File APIs are not fully supported in this browser.');
                return
            }
            this.build();
        },
        
        build: function() {
            // Todo: less ugly markup.
            this.dialog = $('<div />');
            this.dialog.attr('title', 'Upload Progress');
            var table = $(' \
                <table class="e2l-shaded e2-upload-table"> \
                    <thead> \
                        <tr> \
                            <th>Filename</th> \
                            <th style="width:80px">Filesize</th> \
                            <th style="width:80px">Progress</th> \
                            <th style="width:30px;"></th> \
                        </tr> \
                    </thead> \
                    <tbody> \
                    </tbody> \
                </table>');
            this.dialog.append(table);
            
            var ok = $('<form method="post" />');
            ok.attr('action', this.options.action);
            ok.appendTo(this.dialog);
            
            if (this.options.modal) {
                this.dialog.dialog({
                    width: 600,
                    height: 600,
                    draggable: false,
                    resizable: false,                    
                    autoOpen: false,
                    modal: true,
                    closeOnEscape: false,
                    dialogClass: 'e2-dialog-no-close',
                    buttons: {
                        "Preparing for upload": function() {
                            $('form', this).submit();
                        }
                    }
                });
            } else {
                ok.append('<ul class="e2l-controls"><li><input type="submit" value="Uploading" disabled="disabled" /></li></ul>');
                this.element.append(this.dialog);
            }

            this.dialog.append(ok);

        },        
        
        submit: function(e) {
            var self = this;

            // Clear the table body
            $('.e2-upload-table tbody', this.dialog).empty();
            
            // Show the dialog
            this.dialog.dialog('open');
            
            // Show completion button
            $('.e2-dialog-no-close button').attr('disabled','disabled');
            $('.e2-dialog-no-close button .ui-button-text').text("Uploading...");

            // Get the files and parameter name
            var fileinput = $('input:file', this.element);
            var files = fileinput[0].files;
            var param = fileinput.attr('name');
            if (param) {this.options.param = param}

            // Add each file to the table and upload
            $.each(files, function(index, file) {
                self.add(index, file);
            });
            
            // Start the upload
            this.next(0);
        },
        
        add: function(index, file) {
            // Add to the file queue
            this.files.push([index, file]);
            var tbody = $('.e2-upload-table tbody', this.dialog);
            var row = $('<tr />');
            row.attr('data-index', index);
            $('<td />').text(file.name).appendTo(row);
            $('<td />').text(emen2.template.prettybytes(file.size)).appendTo(row);
            $('<td><div style="height:16px" class="e2-upload-progress"></div></td>').appendTo(row);
            $('<td class="e2-upload-action"/>').appendTo(row);
            tbody.append(row);
        },
        
        next: function(wait) {
            var self = this;
            if (wait == null) {wait = this.options.wait}

            // Upload is done.
            if (!this.files.length) {
                $('.e2-dialog-no-close button').attr('disabled',null);
                $('.e2-dialog-no-close button .ui-button-text').text("Upload complete!");
                return
            }

            // Wait a period of time before next upload
            var item = this.files.shift();
            setTimeout(function(){
                self.upload(item[0], item[1]);
            }, wait);
            
        },
        
        retry: function(index, file) {
            this.upload(index, file);
        },
        
        upload: function(index, file) {
            // Upload the file blob
            var self = this;

            // This row
            var elem = $('tr[data-index='+$.escape(index)+'] .e2-upload-progress');
            var action = $('tr[data-index='+$.escape(index)+'] .e2-upload-action');
            elem.empty();
            action.empty();
            
            // Upload destination
            var uri = this.options.action;

            clr = function(elem, action) {
                elem.empty();
                action.empty();
                elem.progressbar('destroy');
            }
            
            // Setup the XHR
            var xhr = new XMLHttpRequest();
            xhr.upload.onprogress = function(e) {
                var prog = Math.round((e.loaded / e.total) * 100);
                elem.progressbar('value', prog);
            }
            xhr.onloadend = function(e) {
                if (this.status == 500) {
                    // Server error
                    clr(elem, action);
                    elem.text('Error');
                    emen2.template.image('retry.png','Retry').click(function(){self.retry(index, file)}).appendTo(action);
                } else if (this.status == 200) {
                    // Successful upload
                    clr(elem, action);
                    elem.text('Completed');
                    emen2.template.image('ok.png','Success').appendTo(action);
                }
                // Always go ahead and try the next item
                self.next()
            }
            xhr.onloadstart = function(e) {
                // Show a cancel action
                clr(elem, action);
                elem.progressbar({});
                emen2.template.image('cancel.png','Cancel').click(function(){xhr.abort()}).appendTo(action);
            }
            xhr.onabort = function(e) {
                // Retry an aborted upload
                clr(elem, action);
                elem.text('Aborted');
                emen2.template.image('retry.png','Retry').click(function(){self.retry(index, file)}).appendTo(action);
            }
            xhr.onerror = function(e) {
                // Retry an upload that failed
                clr(elem, action);
                elem.text('Error');
                emen2.template.image('retry.png','Retry').click(function(){self.retry(index, file)}).appendTo(action);
            }
            xhr.ontimeout = function(e) {
                // Retry after time out
                clr(elem, action);
                elem.text('Timed out');
                emen2.template.image('retry.png','Retry').click(function(){self.retry(index, file)}).appendTo(action);
            }
            // Start the request
            xhr.open('PUT', uri, true);            
            xhr.setRequestHeader('X-File-Name', file.name);
            xhr.setRequestHeader('X-File-Size', file.size);
            xhr.setRequestHeader('X-File-Param', this.options.param);
            xhr.setRequestHeader('Content-Type', file.type);            
            
            // Send the file
            xhr.send(file);
            
        }
    });
    
    
    $.widget("emen2.AttachmentControl", {
        options: {
            name: null,
            edit: false,
            show: true,
            controls: null,
            multiple: true,
            summary: false,
            help: false,
            // events: saved..
        },
                
        _create: function() {
            this.built = 0;
            this.bdos = [];
            this.bdomap = {};
            if (this.options.show) {            
                this.show();
            }
        },

        show: function() {
            this.build();
        },

        build: function() {
            // Find binaries attached to the named record
            var self = this;
            emen2.db("binary.find", {'record':self.options.name}, 
                function(bdos) {
                    self.bdos = bdos;
                    emen2.cache.update(bdos);

                    // Grab all the users we need
                    var users = $.map(self.bdos, function(i){return i['creator']});
                    users = emen2.cache.check('user', users);
                    if (users.length) {
                        emen2.db('user.get', [users], function(users) {
                            emen2.cache.update(users);
                            self._build();
                        });
                    } else {
                        self._build();
                    }
                }
            );            
        },

        _build: function() {
            // Build callback
            if (this.built) {return}
            this.built = 1;
            
            var self = this;
            var dialog = $('<div />');    
            
            // Key the binaries by parameter
            this.bdomap = this.makebdomap(this.bdos);

            if (this.options.summary || this.options.help) {
                this.element.append('<h2 class="e2l-cf">Attachments</h2>');
            }

            if (this.options.help) {
                var help = $(' \
                    <div class="e2l-help" role="help"><p> \
                        To <strong>upload attachments</strong>, click the <strong>browse</strong> button below. \
                        Select the files you want to upload, and a dialog will appear \
                        showing current upload progress. After all the files have \
                        been uploaded, click "Ok" to view the updated record. \
                    </p><p> \
                        To <strong>remove attachments</strong>, uncheck the corresponding checkboxes \
                        and click <strong>save attachments</strong>.  \
                    </p><p>Please note that attachments are never truly deleted; \
                        only the association with the record is removed. The person who originally \
                        uploaded the attachment will still be able to access the attachment. \
                        Additionally, attachments cannot be modified after they \
                        have been created. To make changes, upload a new copy of the file. \
                    </p><p> \
                        Additional information is available at the <a href="http://blake.grid.bcm.edu/emanwiki/EMEN2/Help/Attachments">EMEN2 wiki</a>. \
                    </p></div>');    

                //     There are several types of attachments. The default,
                //     "Regular attachment" (file_binary_image), allows multiple attachments
                //     and is fine for most purposes. Some parameters have special behaviors attached,
                //     such as Image (file_binary_image), which will show an interactive image preview.

                this.element.append(help);
                var helper = $('<span class="e2-button e2l-float-right">Help</span>');
                helper.click(function(e){$('[role=help]', self.element).toggle()})
                $('h4', this.element).append(helper);
            }
            
            if (this.options.summary) {
                var summary = $('<div />');
                var sum2 = $('<p />').text('This record has '+this.bdos.length+' attachments.');
                var rec = emen2.cache.get(this.options.name);
                sum2.append(' There may be additional attachments in child records: ');
                var a = $('<a />')
                a.attr('href', emen2.template.uri(['record', this.options.name, 'query', 'attachments']))
                a.text('view all attachments in child records.');
                a.appendTo(sum2);
                summary.append(sum2);
                this.element.append(summary);
            }

            
            // Build the items
            $.each(this.bdomap, function(k,v) {
                self.element.append(self.build_level(k,k,v))
            });

            this.element.append(dialog);

            if (this.options.controls) {
                this.build_controls();
            }
            
            $('.e2-attachments-infobox').InfoBox('show');
        },

        build_level: function(label, level, items) {
            var self = this;
            var pd = emen2.caches['paramdef'][level];
            if (pd) {label = pd.desc_short}

            // Update the select count when built or checked..
            var cb = function() {$('.e2-select', self.options.controls).SelectControl('update')}            
            var header = $('<h4 />').text(label);
            var d = $('<div class="e2l-cf e2l-fw" />');
            $.each(items, function() {
                // Like other InfoBoxes, don't show until appended to DOM
                var infobox = $('<div class="e2-attachments-infobox" />').InfoBox({
                    show: false,
                    name: this,
                    keytype: 'binary',
                    selectable: self.options.edit,
                    input: ['checkbox', level, true],
                    built: cb,
                    selected: cb
                });
                d.append(infobox);
            });
            $('<input type="hidden" value="" />').attr('name', level).appendTo(d);            
            return $('<div>').append(header, d)
        },

        build_controls: function() {
            var self = this;
            
            // Controls includes it's own form for uploading files
            var controls = $(' \
                <ul class="e2l-options"> \
                    <li>Add attachments: <input type="file" class="e2-attachments-fileinput" name="file_binary" multiple /></li> \
                </ul> \
                <ul class="e2l-controls"> \
                    <li><input type="submit" class="e2l-save" value="Update attachments" /></li> \
                </ul>');

            // Selection control
            $('.e2-select', controls).SelectControl({root: this.element});

            // The submit button saves the form normally
            // $('input:submit', controls).click(function(e){self.save(e)});
            
            // If File API is supported, upload files as soon as files are selected.
            $('.e2-attachments-fileinput', controls).change(function(e) {
                self.save(e);
            });
            
            this.options.controls.append(controls);
        },
        
        save: function(e) {
            this.element.UploadControl({});
            this.element.UploadControl('submit');
        },
        
        // Utility methods --
        makebdomap: function(bdos) {
            // This is to avoid an extra RPC call, and sort BDOs by param name
            var bdomap = {};
            var rec = emen2.caches['record'][this.options.name];
            var self = this;

            $.each(bdos, function(i, bdo) {
                // find bdo in record..
                $.each(rec, function(k,v) {
                    if (typeof(v)=="object" && v != null) {
                        if ($.inArray(bdo.name, v) > -1) {
                            self.bdomap_append(bdomap, k, bdo.name);
                        }
                    } else {
                        if (v==bdo.name) {
                            self.bdomap_append(bdomap, k, bdo.name);
                        }
                    }
                });
            });    
            return bdomap
        },

        bdomap_append: function(bdomap, param, value) {
            if (bdomap[param] == null) {
                bdomap[param] = [];
            }
            bdomap[param].push(value);
        },    
            
    });
})(jQuery);

<%!
public = True
headers = {
    'Content-Type': 'application/javascript',
    'Cache-Control': 'max-age=86400'
}
%>