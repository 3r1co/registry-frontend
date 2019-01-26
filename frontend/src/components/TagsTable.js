import React, { Component } from 'react';
import MaterialTable from 'material-table'
import {CastByteToNumber} from '../helpers.js'

const columns=[
    { title: 'Tag', field: 'tag' },
    { title: 'Size', field: 'sizes', render: rowData => {
        var total = 0
        for(var entry in rowData.sizes) {
            total += rowData.sizes[entry]
        }
        return CastByteToNumber(total)
    }}
]

const options = {};

class TagsTable extends Component {

    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: false,
            items: []
        };
        this.onClick = props.onClick
    }

    setItems(items) {
        this.setState(() => ({
            items: items
        }));
    }


    render() {
        return (
            <MaterialTable
              title={"Tags"}
              data={this.state.items}
              columns={columns}
              options={options}
              onRowClick={this.onClick}
              localization={{
                body: {
                    emptyDataSourceMessage: 'Please select repository first.',
                },
                }}
            />
        );
    }
  }
  export default TagsTable