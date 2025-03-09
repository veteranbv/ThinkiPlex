# Authentication Guide

ThinkiPlex requires authentication data to download course content from Thinkific. This guide explains how to obtain and update this authentication data.

## Required Authentication Data

You need to provide two pieces of authentication data:

1. **Client Date**: The value of the `date` header from a network request
2. **Cookie Data**: The value of the `cookie` header from a network request

## Obtaining Authentication Data

Follow these steps to obtain the required authentication data:

1. **Log in to your Thinkific course**: Open your browser and log in to your Thinkific course
   
2. **Open Developer Tools**:
   - Chrome: Press `F12` or right-click and select "Inspect"
   - Firefox: Press `F12` or right-click and select "Inspect Element"
   - Safari: Enable Developer Tools in Preferences > Advanced, then press `Command+Option+I`

3. **Go to the Network tab**: Click on the "Network" tab in the Developer Tools panel

4. **Refresh the page**: Press `F5` or click the refresh button in your browser

5. **Find a request to your course**:
   - Look for a request with a URL containing `/courses/take/your-course-name`
   - Click on this request to view its details

6. **Find the headers**:
   - Go to the "Headers" section
   - Look for "Request Headers"
   - Find the `date` header and copy its value (this is your **Client Date**)
   - Find the `cookie` header and copy its value (this is your **Cookie Data**)

![Network Headers Example](https://imgur.com/your-screenshot-link.png)

## Adding Authentication Data During Setup

When running the setup wizard (`thinkiplex --setup`), you will be prompted to enter the authentication data. Simply paste the values you copied from the Developer Tools.

## Updating Authentication Data

Authentication data may expire over time. If you encounter download errors, you may need to update your authentication data.

### Using the Interactive Mode

```bash
thinkiplex
```

Then select "Update authentication data" from the menu.

### Using Command-Line Arguments

```bash
thinkiplex --course your-course-name --update-auth --client-date "your-client-date" --cookie-data "your-cookie-data"
```

### Using the Setup Wizard

```bash
thinkiplex --setup
```

Then select "Edit an existing course configuration" and update the authentication data.

## Troubleshooting

If you're having trouble with authentication:

- Make sure you're logged in to your Thinkific course before capturing the headers
- Authentication data expires over time, so you may need to get fresh values
- The entire cookie string can be very long—make sure you copy the complete value
- Some browsers format the headers differently—try copying from a different browser if you have issues

## Security Note

ThinkiPlex stores your authentication data in plain text in the configuration file. This is necessary to authenticate with Thinkific, but it means you should:

- Keep your configuration file secure
- Do not share your configuration file with others
- Consider updating your authentication data periodically for security