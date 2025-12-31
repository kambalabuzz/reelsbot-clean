"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { createSeries } from "@/lib/api";

import Step1Niche from "./steps/step1-niche";
import Step2Voice from "./steps/step2-voice";
import Step3Music from "./steps/step3-music";
import Step4ArtStyle from "./steps/step4-art-style";
import Step5Captions from "./steps/step5-captions";
import Step6Social from "./steps/step6-social";
import Step7Schedule from "./steps/step7-schedule";
import Step8Review from "./steps/step8-review";

const steps = [
  { id: 1, name: "Niche", component: Step1Niche },
  { id: 2, name: "Voice", component: Step2Voice },
  { id: 3, name: "Music", component: Step3Music },
  { id: 4, name: "Art Style", component: Step4ArtStyle },
  { id: 5, name: "Captions", component: Step5Captions },
  { id: 6, name: "Social", component: Step6Social },
  { id: 7, name: "Schedule", component: Step7Schedule },
  { id: 8, name: "Review", component: Step8Review },
];

export type SeriesFormData = {
  // Step 1: Niche
  niche: string;
  customNiche?: string;
  
  // Step 2: Voice
  language: string;
  voice: string;
  
  // Step 3: Music
  musicTracks: string[];
  customMusic?: File;
  
  // Step 4: Art Style
  artStyle: string;
  
  // Step 5: Captions
  captionStyle: string;
  
  // Step 6: Social
  platforms: {
    tiktok: boolean;
    instagram: boolean;
    youtube: boolean;
  };
  
  // Step 7: Schedule
  seriesName: string;
  videoDuration: string;
  postFrequency: string;
  postTime: string;
};

const initialFormData: SeriesFormData = {
  niche: "",
  language: "en",
  voice: "adam",
  musicTracks: [],
  artStyle: "",
  captionStyle: "red_highlight",
  platforms: {
    tiktok: false,
    instagram: false,
    youtube: false,
  },
  seriesName: "",
  videoDuration: "medium",
  postFrequency: "daily",
  postTime: "18:00",
};

export default function CreateSeriesPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<SeriesFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateFormData = (data: Partial<SeriesFormData>) => {
    setFormData((prev) => ({ ...prev, ...data }));
  };

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await createSeries({
        name: formData.seriesName,
        niche: formData.niche,
        language: formData.language,
        voice: formData.voice,
        music_tracks: formData.musicTracks,
        art_style: formData.artStyle,
        caption_style: formData.captionStyle,
        platforms: formData.platforms,
        video_duration: formData.videoDuration,
        post_frequency: formData.postFrequency,
        post_time: formData.postTime,
      });
      router.push("/dashboard/series");
    } catch (error) {
      console.error("Error creating series:", error);
      setError("Unable to create series. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const CurrentStepComponent = steps[currentStep - 1].component;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                  currentStep > step.id
                    ? "bg-primary text-primary-foreground"
                    : currentStep === step.id
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                )}
              >
                {currentStep > step.id ? (
                  <Check className="h-4 w-4" />
                ) : (
                  step.id
                )}
              </div>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    "w-full h-1 mx-2 rounded transition-colors",
                    currentStep > step.id ? "bg-primary" : "bg-muted"
                  )}
                  style={{ width: "60px" }}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            Step {currentStep} of {steps.length}
          </span>
          <span className="text-sm text-muted-foreground">
            — {steps[currentStep - 1].name}
          </span>
        </div>
      </div>

      {/* Step content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
        >
          <CurrentStepComponent
            formData={formData}
            updateFormData={updateFormData}
          />
        </motion.div>
      </AnimatePresence>

      {error && (
        <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8 pt-6 border-t">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={currentStep === 1}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>

        {currentStep < steps.length ? (
          <Button onClick={nextStep} className="gap-2">
            Continue
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                Creating...
              </>
            ) : (
              <>
                Create Series
                <Check className="h-4 w-4" />
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
