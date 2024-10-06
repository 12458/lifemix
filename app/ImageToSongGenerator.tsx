"use client";
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Download, Music, Plus, Upload, X, Loader2 } from 'lucide-react';
import { useState } from 'react';
import GradualSpacing from "@/components/ui/gradual-spacing";




const ImageToSongGenerator = () => {
  const [images, setImages] = useState<{ file: File; preview: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  interface Result {
    title: string;
    genre_tags: string[];
    song_bpm: number;
    language: string;
    singer: string;
    lyrics: string;
    audio_url: string;
  }
  
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bpm, setBpm] = useState(120);
  const [currentTag, setCurrentTag] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [language, setLanguage] = useState('en');
  const [singer, setSinger] = useState('random');
  const [downloadStatus, setDownloadStatus] = useState({ ready: false, audio_url: null });

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) return;
    const files = Array.from(event.target.files);
    const newImages = files.map(file => ({
      file: file as File,
      preview: URL.createObjectURL(file as Blob)
    }));
    setImages(prevImages => [...prevImages, ...newImages]);
  };

  const handleImageDelete = (index: number) => {
    setImages(prevImages => prevImages.filter((_, i) => i !== index));
  };

  const handleAddTag = () => {
    if (currentTag.trim() !== '' && !tags.includes(currentTag.trim())) {
      setTags(prevTags => [...prevTags, currentTag.trim()]);
      setCurrentTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(prevTags => prevTags.filter(tag => tag !== tagToRemove));
  };

  const pollDownloadStatus = async (songId: string) => {
    try {
      const response = await fetch(`https://novel-gibbon-related.ngrok-free.app/download?id=${songId}`);
      const data = await response.json();
      if (data.ready) {
        setDownloadStatus({ ready: true, audio_url: data.audio_url });
        return true; // Polling can stop
      }
      return false; // Continue polling
    } catch (error) {
      console.error('Error polling download status:', error);
      return true; // Stop polling on error
    }
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setDownloadStatus({ ready: false, audio_url: null });

    const formData = new FormData();
    images.forEach(image => formData.append('images', image.file));

    // Add BPM, tags, language, and singer as JSON
    const metaData = {
      bpm: bpm,
      tags: tags,
      language: language,
      singer: singer
    };
    formData.append('metadata', JSON.stringify(metaData));

    try {
      const response = await fetch('https://novel-gibbon-related.ngrok-free.app/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      // Start polling for download URL
      const pollInterval = setInterval(async () => {
        const finished = await pollDownloadStatus(data.id);
        if (finished) {
          clearInterval(pollInterval);
        }
      }, 10000); // Poll every 10 seconds
    } catch (error) {
      console.error('Error:', error);
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="max-w-4xl mx-auto p-6">
        <GradualSpacing
          className="font-display text-center text-3xl font-bold -tracking-widest mb-6 text-center text-black dark:text-white md:text-7xl md:leading-[5rem]"
          text="LifeMix"
        />
        <div className="mb-6">
          <input
            type="file"
            accept=".jpg,.jpeg,.mp4"
            multiple
            onChange={handleImageUpload}
            className="hidden"
            id="image-upload"
          />
          <label
            htmlFor="image-upload"
            className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50"
          >
            <div className="text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-1 text-sm text-gray-600">Click to upload images</p>
            </div>
          </label>
        </div>

        {images.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
            {images.map((image, index) => (
              <div key={index} className="relative">
                {image.file.type === "image/jpeg" ? (
                  <img
                    src={image.preview}
                    alt={`Uploaded ${index + 1}`}
                    className="w-full h-32 object-cover rounded-lg"
                  />
                ) : (
                  <video
                    src={image.preview}
                    className="w-full h-32 object-cover rounded-lg"
                  />
                )}
                <button
                  onClick={() => handleImageDelete(index)}
                  className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="mb-6">
          <label htmlFor="bpm" className="block text-sm font-medium text-gray-700 mb-1">BPM: {bpm}</label>
          <Slider
            id="bpm"
            min={60}
            max={200}
            step={1}
            value={[bpm]}
            onValueChange={(value) => setBpm(value[0])}
            className="w-full"
          />
        </div>

        <div className="mb-4">
          <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">Genre Tags</label>
          <div className="flex items-center mb-2">
            <Input
              type="text"
              id="tags"
              value={currentTag}
              onChange={(e) => setCurrentTag(e.target.value)}
              placeholder="Enter a genre tag"
              className="flex-grow mr-2"
            />
            <Button onClick={handleAddTag} size="sm">
              <Plus size={16} />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, index) => (
              <Badge key={index} variant="secondary" className="px-2 py-1">
                {tag}
                <button onClick={() => handleRemoveTag(tag)} className="ml-2 text-xs">
                  <X size={12} />
                </button>
              </Badge>
            ))}
          </div>
        </div>

        <div className="mb-6 flex space-x-4">
          <div className="flex-1">
            <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">Language</label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="es">Spanish</SelectItem>
                <SelectItem value="fr">French</SelectItem>
                <SelectItem value="de">German</SelectItem>
                <SelectItem value="it">Italian</SelectItem>
                <SelectItem value="ja">Japanese</SelectItem>
                <SelectItem value="ko">Korean</SelectItem>
                <SelectItem value="zh">Chinese</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex-1">
            <label htmlFor="singer" className="block text-sm font-medium text-gray-700 mb-1">Singer</label>
            <Select value={singer} onValueChange={setSinger}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select singer type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="random">Random</SelectItem>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>


        <Button
          onClick={handleSubmit}
          disabled={images.length === 0 || isLoading}
          className="w-full py-3 text-lg font-semibold"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Song...
            </>
          ) : (
            'Generate Song'
          )}
        </Button>

        {error && (
          <Alert variant="destructive" className="mt-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {result && (
          <div className="mt-6 p-4 bg-gray-100 rounded-lg">
            <h2 className="text-2xl font-bold mb-2">{result.title}</h2>
            <p className="mb-2"><strong>Genre Tags:</strong> {result.genre_tags.join(', ')}</p>
            <p className="mb-2"><strong>BPM:</strong> {result.song_bpm}</p>
            <p className="mb-2"><strong>Language:</strong> {result.language}</p>
            <p className="mb-4"><strong>Singer:</strong> {result.singer}</p>
            <h3 className="text-xl font-semibold mb-2">Lyrics:</h3>
            <p className="whitespace-pre-wrap mb-4">{result.lyrics}</p>
            <div className="flex items-center space-x-2 bg-white p-2 rounded-md">
              <Music className="text-blue-500" />
              <audio controls src={result.audio_url} className="w-full" />
            </div>
            <a
              href={downloadStatus.audio_url || undefined}
              download
              className={`mt-4 w-full py-2 flex items-center justify-center ${!downloadStatus.ready ? 'opacity-50 cursor-not-allowed' : ''
                } ${!downloadStatus.ready ? 'pointer-events-none' : ''}`}
            >
              <Button>
                <Download className="mr-2" />
                {downloadStatus.ready ? 'Download Audio' : 'Preparing Download...'}
              </Button>
            </a>
          </div>
        )}

      </div>
    </>
  );
};

export default ImageToSongGenerator;