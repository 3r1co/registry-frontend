import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import classnames from 'classnames';
import Card from '@material-ui/core/Card';
import CardHeader from '@material-ui/core/CardHeader';
import CardContent from '@material-ui/core/CardContent';
import CardActions from '@material-ui/core/CardActions';
import Collapse from '@material-ui/core/Collapse';
import Avatar from '@material-ui/core/Avatar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import red from '@material-ui/core/colors/red';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import MoreVertIcon from '@material-ui/icons/MoreVert';
import CircularProgress from '@material-ui/core/CircularProgress';
import Grid from '@material-ui/core/Grid';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';
import Snackbar from '@material-ui/core/Snackbar';

import ReactJson from 'react-json-view'

import {CastByteToNumber} from '../helpers.js'

const styles = theme => ({
  card: {
  },
  media: {
    height: 0,
    paddingTop: '56.25%', // 16:9
  },
  actions: {
    display: 'flex',
  },
  expand: {
    transform: 'rotate(0deg)',
    marginLeft: 'auto',
    transition: theme.transitions.create('transform', {
      duration: theme.transitions.duration.shortest,
    }),
  },
  expandOpen: {
    transform: 'rotate(180deg)',
  },
  avatar: {
    backgroundColor: red[500],
  },
});

class ManifestCard extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: true,
            tag: null,
            manifest: null,
            expanded: false,
            cardHeader: "Please select Repository and Tag",
            size: "---",
            anchorEl: null,
            notificationOpen: false
        };
    }

  handleExpandClick = () => {
    this.setState(state => ({ expanded: !state.expanded }));
  };

  handleClick = event => {
    this.setState({ anchorEl: event.currentTarget });
  };

  handleClose = () => {
    this.setState({ anchorEl: null });
  };

  openNotification = () => {
    this.setState({ notificationOpen: true });
  }

  closeNotification = () => {
    this.setState({ notificationOpen: false });
  }

  setManifest(tag) {

    this.setState(() => ({
      isLoaded: false,
      manifest: null
    }));

    var encodedRepo = encodeURIComponent(tag.repo)
    var encodedTag = encodeURIComponent(tag.tag)
    fetch(`/api/manifest/${encodedRepo}/${encodedTag}`)
      .then(res => res.json())
      .then((result) => {

          if(typeof result !== 'object') {
            result = JSON.parse(result)
          }

          this.setState(() => ({
              manifest: result,
              isLoaded: true
          }));
      },
      (error) => {
          this.setState({
          isLoaded: true,
          error
      });
      }
    )

    var total =0
    for(var entry in tag.sizes) {
            total += tag.sizes[entry]
    }
    this.setState(() => ({
        cardHeader: tag.repo + ":" + tag.tag,
        size: CastByteToNumber(total)
    }));

   }

  render() {
    const { classes } = this.props;
    const { anchorEl } = this.state;

    return (
      <Card className={classes.card}>
        <CardHeader
          avatar={
            <Avatar aria-label="Recipe" className={classes.avatar}>
              {this.state.cardHeader.substring(0, 1).toUpperCase()}
            </Avatar>
          }
          action={
            <IconButton
            aria-owns={anchorEl ? 'simple-menu' : undefined}
            aria-haspopup="true"
            disabled={this.state.manifest == null}
            onClick={this.handleClick} >
              <MoreVertIcon />
            </IconButton>
          }
          title={this.state.cardHeader}
          subheader={this.state.size} >
        </CardHeader>
        <CardContent>
        <Typography paragraph>
        {!this.state.isLoaded && (
          <Grid container justify = "center">
            <CircularProgress />
          </Grid>
        )}
        { this.state.manifest != null ? <ReactJson src={this.state.manifest} /> : null }
        </Typography>
        </CardContent>
        <CardActions className={classes.actions} disableActionSpacing>
          <IconButton
            className={classnames(classes.expand, {
              [classes.expandOpen]: this.state.expanded,
            })}
            onClick={this.handleExpandClick}
            aria-expanded={this.state.expanded}
            aria-label="Show more"
          >
            <ExpandMoreIcon />
          </IconButton>
        </CardActions>
        <Collapse in={this.state.expanded} timeout="auto" unmountOnExit>
          <CardContent>
            <Typography paragraph>Vulnerabilites:</Typography>
            <Typography paragraph>

            </Typography>
            <Typography>

            </Typography>
          </CardContent>
        </Collapse>
        <Menu
          id="simple-menu"
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={this.handleClose}
          >
        <MenuItem onClick={this.openNotification}>Trigger Vulnerability Scan</MenuItem>
        <MenuItem onClick={this.openNotification}>Transfer</MenuItem>
        <MenuItem onClick={this.openNotification}>Delete</MenuItem>
        </Menu>
        <Snackbar
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'left',
          }}
          open={this.state.notificationOpen}
          autoHideDuration={2000}
          onClose={this.closeNotification}
          ContentProps={{
            'aria-describedby': 'message-id',
          }}
          message={<span id="message-id">Not yet implemented.</span>}
        />
      </Card>
    );
  }
}

ManifestCard.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(ManifestCard);