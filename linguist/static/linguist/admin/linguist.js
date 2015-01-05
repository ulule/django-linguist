(function($) {

    $(function() {

        function field_class(field, language) {
            return '.form-row.field-' + field + '_' + language;
        }

        fields = window.linguist.translatable_fields;
        default_language = window.linguist.default_language;

        fields.forEach(function(field) {
            $(field_class(field, default_language)).hide();
        });

    });

})(django.jQuery);
