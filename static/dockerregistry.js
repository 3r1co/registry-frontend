$.fn.dataTable.render.byteconversion = function ( cutoff ) {
    return function ( data, type, row ) {
        if ( type === 'display' ) {
            var fileSizeInBytes = data.toString(); // cast numbers
 
            var i = -1;
            var byteUnits = [' kB', ' MB', ' GB', ' TB', 'PB', 'EB', 'ZB', 'YB'];
            do {
                fileSizeInBytes = fileSizeInBytes / 1024;
                i++;
            } while (fileSizeInBytes > 1024);
        
            return Math.max(fileSizeInBytes, 0.1).toFixed(1) + byteUnits[i];
        }
 
        // Search, order and type can use the original data
        return data;
    };
};

$(document).ready(function() {
    $('#repositories').DataTable( {
        "ajax": "repositories.json",
        "columns": [
            { "data": "repo" },
            { "data": "tags" },
            { "data": "size" , render: $.fn.dataTable.render.byteconversion( 3 )}
          ]
    }
    );
} )