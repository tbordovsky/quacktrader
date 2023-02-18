### oauth2.0
The TD-Ameritrade API allows applications to authenticate with it using OAuth2.0. This means that an application must request permission to interface with that API
on behalf of a user. The `tda-api` library used in this project provides a few different ways to complete this authentication workflow. The easiest way uses selenium
to automatically step through the browser workflow and then provides an authenticated http client that is ready to make requests.

Unfortunately this doesn't seem to work in my wsl2 environment because of course it doesn't. So I've opted to use the manual workflow, by which I can follow some
simple instructions and interact with my browser and terminal to complete the process.

### selenium
In case you've opted for the easy way to authenticate (kudos!), the selenium dependency is not self-contained. You'll need a platform-specific installation of webdriver that matches whichever version of whichever browser 
you want to use.