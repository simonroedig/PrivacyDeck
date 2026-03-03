give me a good markdown file for github for our project PrivacyDeck
in the course PPS (practical privacy and security) at LMU Munich, involved
where Franziska Oberländer, Mustafa Durani, Tristan Häuser and Simon Rödig (me).


we can write somehtibng like this:
Although privacy tools exist, they are buried in complex, fragmented OS settings with no unified control dashboard or immediate feedback. This leads to underuse of protective features in favour of convenience and exposes users to risks such as unauthorized camera or mic access and data leaks during everyday computing

PrivacyDeck envisions a world where privacy protection requires no effort where awareness alone is enough and no one ever has to worry about an 
embarrassing moment again

So the privacydeck= A compact, USB-connected physical control panel that provides tangible, intuitive control over core privacy functions
personalized to you via an avatar

in the very beginning we can inlcude snapshot.jpg

maybe a bit below then also the snapshot_all_functions.jpg
that shows what each button/toggle/slider/display really does

to the code:
we have built at first a vertical prototype, code in folder verticalPrototype
lets also include the image vertical_prototype.png

included is also the folder 3d showing all used 3d assets, like the avatar
the folder lasercut showing the laser cut files we used for the privacydeck

also include the pinout.png showing the pinout for the raspbeery pi pico

final code of a working demo in folder privacyDeck, subfolder os
where the python daemon is (final_main_os), we recommend Linux, as the final
was tested on linux (zorinOs), windows 11 can also be used
however, a lot of graphical gui approaches to trigger certain functions,
macos was not tested, but is at parts integrated.
folder piPico in privacyDeck shows the final_main_pico a demo to test
it on the pico, they communicate with the python daemon via serial,
so it is important to load it onto the main file on the pico
and give free the port so that it can communicate wehen starting the final_main_os

also a folder called guisoftware, showing a prototype of a software for real graphical
OS daemon with visible what privacy/secudity functiosn are active, a digital avatar
to customize and configuration of toggles and buttons. we can inlcude gui_snapshot.png here