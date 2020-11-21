# SelfVPN

## Docs
#### API methods
___
1. `POST` `/get`
    * __Description:__
        Returns openvpn config by country and login data
    * __Input parameters:__
        - `uid` - client id
        - `token` - client access token
        - `country` (_optional_) - country of VPN server
    * __Output parameters:__
        - `code` - response code
        - `msg` - status message
        - `config` - base64 encoded openvpn config
1. `POST` `/push`
    * __Description:__
        Updates port or/and ip for client by login data
    * __Input parameters:__
        - `uid` - client id
        - `token` - client access token
        - `port` - new port number
    * __Output parameters:__
        - `code` - response code
        - `msg` - status message
1. `POST` `/update`
    * __Description:__
        Updates config for some slot by login data
    * __Input parameters:__
        - `uid` - client id
        - `token` - client access token
        - `slot` - slot number
        - `config` - base64 encoded openvpn config
    * __Output parameters:__
        - `code` - response code
        - `msg` - status message
1. `POST` `/register`
    * __Description:__
        Registers new client
    * __Input parameters:__
        - `port` - port
    * __Output parameters:__
        - `code` - response code
        - `msg` - status message
        - `uid` - new user id
        - `token` - access token
1. `POST` `/heartbeat`
    * __Description:__
        Saves timestamp of ping to database. Needed to check if client is dead.
    * __Input parameters:__
        - `uid` - client id
        - `token` - client access token
    * __Output parameters:__
        - `code` - response code
        - `msg` - status message

#### Response codes
___
 - `0` - OK
 - `1` - auth error
 - `2` - malformed data
 - `3` - internal error

#### Contacts
None :)
