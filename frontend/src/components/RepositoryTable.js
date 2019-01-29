import React, { Component } from 'react';
import MaterialTable from 'material-table'
import {CastByteToNumber} from '../helpers.js'

const columns=[
    { title: 'Repository', field: 'repo' },
    { title: '# of tags', field: 'tags' , type: 'numeric'},
    { title: 'Size', field: 'size', render: rowData => {
        return CastByteToNumber(rowData.size)
    }, defaultSort: 'desc' }
]

const options = {
    pageSize: 10
};

class RepositoryTable extends Component {

    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: false,
            items: []
        };
        this.onClick = props.onClick
    }

    componentDidMount() {
        fetch("/api/repositories")
            .then(res => res.json())
            .then((result) => {

                this.setState({
                    isLoaded: true,
                    items: result.data
                });
            },
            (error) => {
                this.setState({
                isLoaded: true,
                error
            });
            }
        )
    }



  render() {
    return (
        <MaterialTable
          title={"Repositories"}
          data={this.state.items}
          columns={columns}
          options={options}
          onRowClick={this.onClick}
          localization={{
            body: {
                emptyDataSourceMessage: 'Loading repositories...',
            },
            }}
        />
    );
  }
  }
  export default RepositoryTable