import React from 'react';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faFile } from '@fortawesome/free-solid-svg-icons'


class Protocol extends React.Component {
  constructor(props) {
    super(props);
  }


  handleDragStart = (e) => {
    e.dataTransfer.setData('hcaId', this.props.hcaId);
    e.dataTransfer.setData('originatingPoolId', this.props.poolId);
    console.log('dragstart', e.dataTransfer.getData('hcaId'));
  };


  render() {
    const { hcaId, description } = this.props;

    return (
      <div
        title={description}
        className="flex items-center text-left text-ellipsis border-warning bg-dark fg-light m-xs"
        onDragStart={this.handleDragStart}
        draggable
      >
        <FontAwesomeIcon className="mx-xs fg-light" icon={faFile} />
        <small className="mx-xs fg-light">{hcaId}</small>
      </div>
    );
  }
}


export default Protocol;
