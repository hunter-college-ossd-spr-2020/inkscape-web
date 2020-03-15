/**
 * @license Copyright (c) 2003-2019, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here.
	// For complete reference see:
	// https://ckeditor.com/docs/ckeditor4/latest/api/CKEDITOR_config.html

	// Additional plugins
	// (most should be included in the optimized version of ckeditor.js where possible, see build-config.js)
	//
	// exceptions as they're customized for inkscape.org:
	// - "blockquote" - direct citing (with backlinks) of highlighted text on forum pages
	// - "codeTag"    - better version that properly escapes code
	// - "emoji"      - adds a list of recently used emoji
	config.extraPlugins = 'blockquote,codeTag,emoji';

	// The toolbar groups arrangement, optimized for a single toolbar row.
	config.toolbarGroups = [
		{ name: 'document',    groups: [ 'document', 'doctools' ] },
		{ name: 'clipboard',   groups: [ 'clipboard', 'undo' ] },
		{ name: 'editing',     groups: [ 'find', 'selection', 'spellchecker' ] },
		{ name: 'forms' },
		{ name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
		{ name: 'paragraph',   groups: [ 'list', 'indent', 'blocks', 'align', 'bidi' ] },
		{ name: 'links' },
		{ name: 'insert' },
		{ name: 'styles' },
		{ name: 'colors' },
		{ name: 'tools' },
		{ name: 'others' ,     groups: [ 'mode' ] },
		{ name: 'about' }
	];

	// The default plugins included in the basic setup define some buttons that
	// are not needed in a basic editor. They are removed here.
	// config.removeButtons = 'Cut,Copy,Paste,Undo,Redo,Anchor,Underline,Strike,Subscript,Superscript';
	config.removeButtons = 'Anchor,Save';

	// Dialog windows are also simplified.
	config.removeDialogTabs = 'link:advanced';

	// More custom config
	config.disallowedContent = 'a[on*]';
	config.disableNativeSpellChecker = false;
	config.codeSnippet_theme = 'github';

    // Customized shortcuts
    config.keystrokes = [
        [ CKEDITOR.CTRL + 13, 'save' ], // Ctrl+Enter for submitting post
    ];
};
