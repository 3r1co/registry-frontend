import React, { Component } from 'react';
import Grid from '@material-ui/core/Grid';
import NavBar from './components/NavBar'
import RepositoryTable from './components/RepositoryTable'
import TagsTable from './components/TagsTable'
import ManifestCard from './components/ManifestCard'

import 'typeface-roboto';

class App extends Component {

    constructor(props) {
        super(props);
        this.tagTable = React.createRef();
        this.manifestCard = React.createRef();
    }

    clickRepository = (event, rowData) => {
        this.tagTable.current.setRepo(rowData.repo)
    }

    clickTag = (event, rowData) => {
        this.manifestCard.current.setManifest(rowData)
    }

    render() {
        return (
            <div>
                <NavBar />
                <Grid container spacing={24} style={{padding: 24}}>
                    <Grid item xs>
                        <RepositoryTable onClick={this.clickRepository} />
                    </Grid>
                    <Grid item xs>
                        <TagsTable ref={this.tagTable} onClick={this.clickTag} />
                    </Grid>
                    <Grid item xs>
                        <ManifestCard innerRef={this.manifestCard} />
                    </Grid>
                </Grid>
            </div>
        );
    }
}

export default App;
