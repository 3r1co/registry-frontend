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

import {CastByteToNumber} from '../helpers.js'

const styles = theme => ({
  card: {
    //maxWidth: 400,
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
            isLoaded: false,
            tag: null,
            manifest: null,
            expanded: false,
            cardHeader: "Please select Repository and Tag",
            size: ""
        };
    }

  handleExpandClick = () => {
    this.setState(state => ({ expanded: !state.expanded }));
  };

  setManifest(tag) {
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

    return (
      <Card className={classes.card}>
        <CardHeader
          avatar={
            <Avatar aria-label="Recipe" className={classes.avatar}>
              {this.state.cardHeader.substring(0, 1).toUpperCase()}
            </Avatar>
          }
          action={
            <IconButton>
              <MoreVertIcon />
            </IconButton>
          }
          title={this.state.cardHeader}
          subheader={this.state.size}
        />
        <CardContent>
          <Typography component="p">

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
            <Typography paragraph>

            </Typography>
            <Typography>

            </Typography>
          </CardContent>
        </Collapse>
      </Card>
    );
  }
}

ManifestCard.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(ManifestCard);