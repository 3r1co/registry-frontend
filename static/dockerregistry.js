$.fn.dataTable.render.byteconversion = function () {
    return function ( data, type, row ) {
        if ( type === 'display' ) {
            var fileSizeInBytes = data.toString(); // cast numbers
            return castByteToNumber(fileSizeInBytes)
        }
        // Search, order and type can use the original data
        return data;
    };
};

$.fn.dataTable.render.length = function () {
    return function ( data, type, row ) {
        if ( type === 'display' ) {
            return data.length;
        }
        // Search, order and type can use the original data
        return data;
    };
};

function castByteToNumber(fileSizeInBytes) {
    var i = -1;
    var byteUnits = [' kB', ' MB', ' GB', ' TB', 'PB', 'EB', 'ZB', 'YB'];
    do {
        fileSizeInBytes = fileSizeInBytes / 1024;
        i++;
    } while (fileSizeInBytes > 1024);

    return Math.max(fileSizeInBytes, 0.1).toFixed(1) + byteUnits[i];
}

function sum(images) {
    var sum = 0;
    for( var image in images ) {
        if(images[image]["size"]) {
            sum += parseFloat(images[image]["size"]);
        }
    }
    return sum;
  }

$(document).ready(function() {

    $.getJSON( "/repositories.json", function(data) {
        $('#information').text(`Proudly serving ${castByteToNumber(sum(data.data))} of images!`)
        $('#repositories').DataTable( {
            "data": data.data,
            "columns": [
                { "data": "repo" },
                { "data": "tags" , render: $.fn.dataTable.render.length()},
                { "data": "size" , render: $.fn.dataTable.render.byteconversion() }
              ],
            "order": [[ 2, "desc" ]]
        }
        );
      });
} )