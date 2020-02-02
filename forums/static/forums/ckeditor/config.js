CKEDITOR.editorConfig = function( config ) {
        config.plugins = 'basicstyles,dialogui,dialog,notification,button,toolbar,clipboard,enterkey,entities,floatingspace,wysiwygarea,indent,indentlist,fakeobjects,link,list,undo,youtube,textwatcher,autocomplete,textmatch,xml,ajax,mentions,panelbutton,panel,floatpanel,emoji,listblock,richcombo,format,codeTag,blackquote,colorbutton,autolink,maximize';
        config.extraPlugins = 'codesnippet';
	config.toolbarGroups = [
		{ name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
		{ name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
		{ name: 'editing', groups: [ 'find', 'selection', 'spellchecker', 'editing' ] },
		{ name: 'forms', groups: [ 'forms' ] },
		{ name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
		{ name: 'paragraph', groups: [ 'list', 'indent', 'blocks', 'align', 'bidi', 'paragraph' ] },
		{ name: 'links', groups: [ 'links' ] },
		{ name: 'insert', groups: [ 'insert' ] },
		{ name: 'styles', groups: [ 'styles' ] },
		{ name: 'colors', groups: [ 'colors' ] },
		{ name: 'tools', groups: [ 'tools' ] },
		{ name: 'others', groups: [ 'others' ] },
		{ name: 'about', groups: [ 'about' ] },
		{ name: 'codesnippet', groups: [ 'codesnippet' ] },
	];

        config.codeSnippet_theme = 'github';
	config.removeButtons = 'Undo,Redo,Anchor,Subscript,Superscript';
};
