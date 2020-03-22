# How to Demo the Transcriber App

### Home Page

Application secured with API key configurable in CloudFormation parameters

### Video Assets Table

Videos with `_Vocabulary` in the name are duplicates of the video we uploaded to have the before and after versions (need to change name of upload video), normally would just reprocess the video

### Video Player

###### Vocabulary Acronyms:

*Astronaut_Radiation*:

Great to show use case for vocabulary. Multiple acronyms throughout video have not been correctly transcribed (SEPs, DNA, CCMC). Show the confidence highlighting to easily point out incorrect captions

*Astronaut_Radiation_Vocabulary*:

Reprocessed video with custom vocabulary fixes acronyms in multiple places throughout video, show the correction at:

    3 seconds
    12 seconds
    17 seconds
    28 seconds
    32 seconds
    38 seconds
    52 seconds
    59 seconds

Can show tweaks expanding acronym by adding this to the tweaks page

    s.e.p.=solar energetic particle
    s.e.p.s.=solar energetic particles.
    s.e.p.s=solar energetic particles

*Rocket_Science*

SLS acronym for the Space Launch System

*Rocket_Science_Vocabulary*

Corrected at:
    
    7 seconds
    36 seconds

Can show tweaks expanding acronym by adding this line to the tweaks page

    s.l.s.=Space Launch System

###### Vocabulary Names:

Smaller use cases for vocabulary with names

*Milky_Way*:

Good to show use case for vocabulary with proper nouns Eli Bressert

*Milky_Way_Vocabulary*:

Corrected at:

    17 seconds
    20 seconds

###### Interesting video

*Life_on_Mars*:

General understanding of video player

### Vocabulary

Use the following custom vocabulary

    AWS
    Bressert
    CCMC
    DNA
    Marshall
    Meier
    S.E.P.
    S.E.P.s
    S.L.S.
    Walt

### Tweaks

Application side post processing which can be used to expand acronyms or adjust casing issues

Can expand the acronyms in the `astronaut_radiation_vocabulary` video