# Dashboard Share Functionality

## Overview

The dashboard share functionality allows users to capture screenshots of their wellness dashboard cards and share them with the Ki Wellness branding. When a user clicks the share icon on any dashboard card, the system captures a screenshot, adds the Ki Wellness logo, and provides sharing options.

## Features

### 🎯 **Core Functionality**
- **Screenshot Capture**: Uses html2canvas library to capture high-quality screenshots
- **Logo Overlay**: Automatically adds the Ki Wellness logo to the bottom center of shared images
- **Multiple Sharing Options**: Native sharing API with fallback download option
- **Loading States**: Visual feedback during screenshot generation
- **Error Handling**: Graceful error handling with user-friendly messages

### 🎨 **Visual Enhancements**
- **Professional Styling**: Clean white background with subtle gradient
- **Shadow Effects**: Adds depth and professionalism to shared images
- **Logo Positioning**: Logo placed at bottom center with subtle background
- **High Resolution**: 3x scale for crisp, high-quality images

### ♿ **Accessibility Features**
- **ARIA Labels**: Proper accessibility attributes for screen readers
- **Keyboard Navigation**: Focus states and keyboard accessibility
- **Tooltips**: Descriptive tooltips for better user experience

## Implementation Details

### **Share Button Structure**
```html
<button class="share-btn absolute top-3 right-3 p-3 text-gray-500 hover:text-mint-green transition-all duration-200 opacity-0 group-hover:opacity-100 md:opacity-0 md:group-hover:opacity-100 z-10 bg-white bg-opacity-90 rounded-full shadow-sm hover:shadow-md active:scale-95 focus:outline-none focus:ring-2 focus:ring-mint-green focus:ring-opacity-50" data-tile="water" title="Share Water Intake" aria-label="Share Water Intake">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <!-- Share icon SVG -->
    </svg>
</button>
```

### **Share Functionality**
```javascript
const shareTile = async (tileType) => {
    // 1. Show loading state
    // 2. Capture screenshot using html2canvas
    // 3. Add logo overlay
    // 4. Generate share data
    // 5. Use native sharing API or fallback to download
}
```

### **Logo Integration**
- **Logo Path**: `/static/logo-new.png`
- **Positioning**: Bottom center of the image
- **Size**: 40% of canvas width (max 250px)
- **Background**: Subtle white background with border
- **Error Handling**: Graceful fallback if logo fails to load

## Supported Dashboard Cards

### 1. **Water Intake Card**
- **Data Tile**: `water`
- **Share Title**: "Hydration Progress - Ki Wellness, Self Health Simplified"
- **Share Text**: Includes current water intake amount
- **Emoji**: 💧

### 2. **Macronutrients Card**
- **Data Tile**: `macros`
- **Share Title**: "Nutrition Balance - Ki Wellness, Self Health Simplified"
- **Share Text**: Includes total calories and nutrition insights
- **Emoji**: 🥗

### 3. **Mood Card**
- **Data Tile**: `mood`
- **Share Title**: "Wellness Check-in - Ki Wellness, Self Health Simplified"
- **Share Text**: Includes current mood and wellness status
- **Emoji**: 😊

## Technical Requirements

### **Dependencies**
- **html2canvas**: For screenshot capture (v1.4.1)
- **Modern Browser**: Native sharing API support
- **Logo File**: `app/static/logo-new.png`

### **Browser Compatibility**
- **Chrome/Edge**: Full support with native sharing
- **Firefox**: Full support with native sharing
- **Safari**: Full support with native sharing
- **Mobile Browsers**: Native sharing API support

### **Fallback Behavior**
- **No Native Sharing**: Automatically downloads the image
- **Logo Load Failure**: Continues without logo overlay
- **Screenshot Failure**: Shows error message to user

## User Experience Flow

### **Desktop Experience**
1. **Hover**: Share button appears on card hover
2. **Click**: Loading spinner appears
3. **Processing**: Screenshot captured and logo added
4. **Share**: Native sharing dialog or download prompt

### **Mobile Experience**
1. **Tap**: Share button responds to touch
2. **Loading**: Visual feedback during processing
3. **Share**: Native sharing sheet appears
4. **Options**: Share to apps, save to photos, etc.

## Customization Options

### **Logo Styling**
```javascript
// Logo size and positioning
const logoWidth = Math.min(250, finalCanvas.width * 0.4);
const logoHeight = (logoWidth * logoImg.height) / logoImg.width;
const logoX = (finalCanvas.width - logoWidth) / 2;
const logoY = finalCanvas.height - logoHeight - 30;

// Logo background
finalCtx.fillStyle = 'rgba(255, 255, 255, 0.95)';
finalCtx.fillRect(logoX - 20, logoY - 15, logoWidth + 40, logoHeight + 30);
```

### **Canvas Styling**
```javascript
// Background gradient
const gradient = finalCtx.createLinearGradient(0, 0, 0, finalCanvas.height);
gradient.addColorStop(0, '#fafbfc');
gradient.addColorStop(1, '#ffffff');

// Shadow effects
finalCtx.shadowColor = 'rgba(0, 0, 0, 0.08)';
finalCtx.shadowBlur = 15;
finalCtx.shadowOffsetX = 0;
finalCtx.shadowOffsetY = 8;
```

## Testing

### **Automated Tests**
Run the test suite to verify functionality:
```bash
python tests/test_dashboard_share.py
```

### **Manual Testing**
1. **Login** to the dashboard
2. **Hover** over dashboard cards to see share buttons
3. **Click** share buttons to test functionality
4. **Verify** logo appears on shared images
5. **Test** sharing on different devices/browsers

### **Test Coverage**
- ✅ Share button presence and accessibility
- ✅ Logo file existence and loading
- ✅ JavaScript function availability
- ✅ Data attribute validation
- ✅ Cross-browser compatibility

## Performance Considerations

### **Optimizations**
- **Parallel Processing**: Screenshot capture doesn't block UI
- **Lazy Loading**: html2canvas loaded on demand
- **Memory Management**: Proper cleanup of canvas objects
- **Error Recovery**: Graceful handling of failures

### **File Sizes**
- **Logo**: ~4.7KB (optimized PNG)
- **Screenshots**: Variable size based on content
- **Final Images**: Typically 100-500KB depending on content

## Security Considerations

### **Data Privacy**
- **Local Processing**: Screenshots generated client-side
- **No Server Upload**: Images not sent to server
- **User Control**: Users choose what to share
- **No Data Collection**: Share actions not tracked

### **Cross-Origin Issues**
- **Logo Loading**: Uses CORS-compatible image loading
- **Error Handling**: Graceful fallback for CORS issues
- **Local Assets**: Logo stored locally to avoid CORS

## Future Enhancements

### **Potential Improvements**
- **Custom Branding**: User-selectable logo options
- **Social Media Integration**: Direct sharing to platforms
- **Image Filters**: Optional styling effects
- **Batch Sharing**: Share multiple cards at once
- **Analytics**: Track sharing engagement (with user consent)

### **Accessibility Improvements**
- **Screen Reader Support**: Enhanced ARIA descriptions
- **Keyboard Shortcuts**: Quick share hotkeys
- **High Contrast Mode**: Better visibility options

## Troubleshooting

### **Common Issues**

#### **Logo Not Appearing**
- Check if `logo-new.png` exists in `app/static/`
- Verify file permissions and accessibility
- Check browser console for CORS errors

#### **Share Button Not Visible**
- Ensure CSS classes are properly applied
- Check for JavaScript errors in console
- Verify hover states work correctly

#### **Screenshot Quality Issues**
- Ensure html2canvas library is loaded
- Check browser compatibility
- Verify canvas scaling settings

#### **Native Sharing Not Working**
- Check browser support for Web Share API
- Verify HTTPS is enabled (required for sharing)
- Test fallback download functionality

### **Debug Mode**
Enable debug logging by adding to browser console:
```javascript
localStorage.setItem('debugShare', 'true');
```

## Support

For issues or questions about the share functionality:
1. Check the troubleshooting section above
2. Review browser console for errors
3. Test with different browsers/devices
4. Contact development team with specific error details
