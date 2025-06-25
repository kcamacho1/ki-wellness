import React from 'react';
import {
    Image,
    Text,
    View,
    Stylesheet,
    TouchableOpacity
} from 'react-native';
import {
    Constants,
    Camera,
    Permissions
} from 'expo';

import {Ionicons} from '@expo/vector-icons';

export default class CameraExample extends React.Component {
    state = {
        hasCameraPermission: null,
        type: Camera.Constants.Type.back,
    };

    async componentDidMount() {
        const {status} = await PErmissions.askAsync(Permissions.CAMERA);
        this.setState({
            hasCameraPErmission: status === 'granted',
        });
    }

render(){
    const {hasCameraPermission} = this.state;

    if (hasCameraPermission === null) {
        return <View><View/>;
    } else if (hasCameraPermission === false){
        return <Text>No access to camera</Text>;
    }
}

// Allow take picture function
takePicture = async => {
    if (this.camera){
        this.camera.takePictureAsync({
            base64: true,
            quality: 0,
            skipProcessing: true
        }).then(image => {
            //detects labels Function
        });
    }
}

// Render Camera View until camera click
render(){
    <View>
    <TouchableOpacity onPress={this.takePicture}>
    <Ionicons name="ios-radio-button-on" size={70} color="white" />
    </TouchableOpacity>
    </View>
}
const requestData = {
    "requests": [
        {
            "image": {
                "content": base64
            },
            "features":[
                {
                    "type": "LABEL_DETECTION",
                    "maxResults": 10
                }
            ]
        }
    ]
}

}