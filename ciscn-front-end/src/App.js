import React, { Component } from 'react';
import logo from './img/The Matrix System.svg';
import './App.css';




class App extends Component {
    constructor(props){
        super(props);
        this.state={
            wifiSniff:true,
            fakeAP:false,
        };
        this.handleSniff = this.handleSniff.bind(this);
        this.handleFakeAP = this.handleFakeAP.bind(this);

    }

   handleSniff(){
        this.setState({wifiSniff:true});
        this.setState({fakeAP:false});
        console.log(this.state);
   }

   handleFakeAP(){
       this.setState({wifiSniff:false});
       this.setState({fakeAP:true});
   }

  render() {
    return (
     <div className="App">
         <Topbar/>

         <div id="right" style={{display:'flex',flexDirection:'column',alignItems:'center'}}>
             <div style={{display:'flex',flexDirection:'row',alignItems:'center',position:'relative',top:'-20px',zIndex:-1}}>
         <LightButton text="Wi-Fi嗅探" handleClick={this.handleSniff} active={this.state.wifiSniff}/>
         <LightButton text="钓鱼AP" handleClick={this.handleFakeAP} active={this.state.fakeAP}/>
             </div>
         </div>
     </div>
    );
  }
}


class Topbar extends Component{
    render(){
        return(
            <div id="Topbar" >
                <img style={{width:'300px'}} src={logo}/>
            </div>
        );
    }
}

class LightButton extends Component{
    constructor(props){
        super(props);
        this.state={
            active:this.props.active,
            text:this.props.text
        };
        this.handleClick = this.handleClick.bind(this);
    }

    handleClick(){
        console.log(this.state.text);
        this.props.handleClick();
    }

    render(){

        return(
            <div className={this.props.active?"light-button light-button-active":"light-button"} onClick={this.handleClick}>
                {this.state.text}
            </div>

        );
    }
}

export default App;
