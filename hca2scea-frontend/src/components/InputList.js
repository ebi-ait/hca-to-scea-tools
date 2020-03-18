import React from 'react';


class InputList extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      listItems: this.props.defaults || [],
    };
  }


  handleClickAddInput = () => {
    if (this.state.listItems.includes('')) {
      return;
    }

    this.setState({ listItems: [...this.state.listItems, ''] });
  };

  handleChangeInput = (index, e) => {
    let newListItems = this.state.listItems;
    newListItems[index] = e.target.value;

    this.setState({ listItems: newListItems }, () => {
      if (newListItems == [] || newListItems.length == 1 && newListItems[0] === '') {
        newListItems = undefined;
      }

      this.props.changeHandler(newListItems);
    });
  }

  handleRemoveInput = (index) => {
    const newListItems = this.state.listItems;
    newListItems.splice(index, 1);

    this.setState({ listItems: newListItems }, () => { this.props.changeHandler(this.state.listItems); });
  }


  componentDidMount = () => {
    if (this.props.defaults) {
      this.props.changeHandler(this.state.listItems);
    }
  }


  render() {
    const {
      handleChangeInput,
      handleClickAddInput,
      handleRemoveInput,
      props: { type, processed },
      state: { listItems },
    } = this;

    return (
      <>
        <input
          type={type}
          value={listItems[0]}
          disabled={processed}
          onChange={(val) => handleChangeInput(0, val)}
        />

        {listItems.slice(1).map((item, index) =>
          <div key={`fragment-${index}`}>
            <input
              key={`input-${index}`}
              type={type}
              value={listItems[index + 1]}
              disabled={processed}
              onChange={(e) => handleChangeInput(index + 1, e)}
            />
            <button
              onClick={() => handleRemoveInput(index + 1)}
              disabled={processed}
              key={`remove-${index}`}
            >
              -
            </button>
          </div>
        )}

        <div>
          <button
            onClick={handleClickAddInput}
            disabled={processed}
          >
            +
          </button>
        </div>
      </>
    );
  }
}


export default InputList;
