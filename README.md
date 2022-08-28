# tg-stable-diffusion

## TODOS:
- [x] Make log messages beatutiful, ex.:
    ```
    --------------
    User: <username>
    time: <time>
    text prompt: <text prompt>
    --------------
    ```
    --> Sasha
- [x] Make `generate_image` return an iterator, to make possible ediding a message with the status, ex.:
    ```
    Generating image... Time elapsed: <number>s.
    ```
    --> Sasha
   
- [ ] Add a persistent object to store all information about all bot users, number of generated images etc. 
- [ ] Add some features, e.g image size, generating more images, increasing number of steps for nn to generate an image.
      More inspiration is here: https://huggingface.co/blog/stable_diffusion
- [ ] Add a dictionary or some kind of a structure (may be an sql database to make this whole more persistent)
      containing information of a user & number of generated images (to make it possible to limit the number of images per day/per hour etc.)
