from fastapi.responses import FileResponse, JSONRespons
@app.get("/get_pfp/{username}")
async def get_pfp(username: str):
    """
    ## Get User Avatar (Profile Picture)
    Allows services to get the avatar (profile picture) of a specified account. 
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Returns:
    - **file:** The avatar the service requested.
    """
    # Checks if the user has a profile pic uploaded
    if os.path.isfile(f"user_images/pfp/{username}"):
        return FileResponse(f"user_images/pfp/{username}", media_type='image/gif')
    else:
        # Returns default image if none is uploaded
        return FileResponse(f'{assets_folder}/default_pfp.png', media_type='image/gif')

@app.get("/get_banner/{username}")
async def get_banner(username: str):
    """
    ## Get User Banner
    Allows services to get the account banner of a specified account.
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Returns:
    - **file:** The banner the service requested.
    """
    # Checks if the user has a profile pic uploaded
    if os.path.isfile(f"user_images/banner/{username}"):
        return FileResponse(f"user_images/banner/{username}", media_type='image/gif')
    else:
        # Returns default image if none is uploaded
        return FileResponse(f'{assets_folder}/default_banner.png', media_type='image/gif')
    
