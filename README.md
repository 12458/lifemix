# Divhacks: LifeMix

## Inspiration

The concept for LifeMix emerged from a desire to encapsulate the emotions behind our cherished memories in a form that goes beyond visual media. While scrolling through photo galleries, we realized the potential of transforming these moments into personalized soundtracks that resonate on a deeper level. This inspired us to create LifeMix—a unique platform that allows users to enrich their experiences by turning their captured moments into custom audio tracks.

## What It Does

LifeMix acts as an intelligent music generator that converts your photos into personalized songs. By analyzing your images based on location, timestamp, and visual content, the app composes a tailored musical piece that aligns with the narrative of your day or special event. The result is a song that captures the essence of your experience, providing a creative and immersive way to relive your memories.

## How We Built It

Building LifeMix required an integration of various technologies to achieve a seamless and engaging user experience:

* **Frontend**: We utilized React and Shadcn UI components to design a responsive and user-friendly interface.
* **Backend**: Powered by Flask, the backend processes, extracts location information and other relevant context and creates the music via Suno, GPT-4o and Gemini-1.5-flash.

We incorporated the following APIs to enhance functionality:

* **Google Maps API**: Extracts metadata from the images, including geolocation and timestamps.
* **OpenAI's GPT-4o**: Generates context-aware lyrics that align with the mood and content of the photos.
* **Gemini-1.5-flash**: Transforms uploaded video context into a context-aware text description for synthesis.
* **Suno API**: Transforms the generated lyrics into a cohesive song by synthesizing melody and vocals.

The combination of these technologies allows LifeMix to dynamically compose unique soundtracks that mirror the essence of users' visual narratives.

## Challenges We Encountered

Several technical and design challenges emerged during development:

1. Synchronizing multiple APIs to function cohesively required extensive troubleshooting and optimization.
2. Extracting meaningful metadata from diverse photo formats posed difficulties in achieving consistent data outputs.
3. Refining AI-generated lyrics to ensure they sounded natural and aligned with user expectations took substantial iteration.
4. Managing user expectations during the song creation process, which can take a few moments, was crucial in maintaining a smooth user experience.

## Accomplishments We’re Proud Of

Despite the complexities, LifeMix has achieved several key milestones:

1. Developed a robust solution that transforms images into high-quality songs with minimal user input.
2. Successfully integrated advanced AI models to generate meaningful, context-aware lyrics and music.
3. Designed a scalable system capable of handling high user volumes without compromising performance.
4. Created a platform that offers genuinely unique, experience-based songs that reflect personal memories.

## Lessons Learned

Our journey with LifeMix offered valuable insights into both technical and creative domains:

1. Mastered the intricacies of managing multiple API integrations to achieve seamless interoperability.
2. Gained a deeper understanding of leveraging AI to enhance creativity and deliver engaging user experiences.
3. Strengthened our full-stack development skills through the implementation of complex frontend and backend systems.
4. Reinforced the importance of thoughtful user experience design when dealing with AI-generated content.

## What’s Next for LifeMix

Looking ahead, we have several enhancements and expansions planned for LifeMix:

1. Enable greater user customization over the generated songs, including genre selection and mood variations.
2. Develop a dedicated mobile application to extend functionality and accessibility.
3. Introduce seamless social media sharing to allow users to showcase their LifeMix creations.
4. Explore collaborations with professional musicians to elevate the musical quality of the generated tracks.
5. Expand the concept to create comprehensive musical journeys that chronicle entire photo libraries.

LifeMix is just the beginning of a new way to experience and share memories through AI-driven music creation. We are excited to continue developing features that make your memories even more meaningful and memorable.

## Running the Project

### Frontend (Next.js)

1. **Install dependencies**:
    ```bash
    cd lifemix
    npm install
    ```

2. **Run the development server**:
    ```bash
    npm run dev
    ```

3. **Build for production**:
    ```bash
    npm run build
    npm start
    ```

### Backend (Flask)

1. **Set up a virtual environment**:
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Flask server**:
    ```bash
    export GOOGLE_MAPS_API_KEY=<YOUR KEY>
    export OPENAI_API_KEY=<YOUR KEY>
    export SUNO_API_BASE_URL=<YOUR URL>
    flask run
    ```

4. **Deactivate the virtual environment**:
    ```bash
    deactivate
    ```

## License

Licensed under the MIT License.

```text
Copyright 2024 Sim Shang En

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```