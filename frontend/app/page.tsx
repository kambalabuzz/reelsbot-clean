"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { 
  Play, Sparkles, Zap, Clock, TrendingUp, Video, 
  Instagram, Youtube, Music, Palette, MessageSquare,
  Check, ArrowRight, Star
} from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Sparkles,
    title: "AI Script Generation",
    description: "Generate engaging scripts for any niche in seconds"
  },
  {
    icon: Palette,
    title: "25+ Art Styles",
    description: "From anime to realistic, choose your visual style"
  },
  {
    icon: MessageSquare,
    title: "Karaoke Captions",
    description: "Word-by-word animated captions that pop"
  },
  {
    icon: Music,
    title: "Background Music",
    description: "20+ preset tracks or upload your own"
  },
  {
    icon: Clock,
    title: "Auto Scheduling",
    description: "Set it and forget it - posts go out automatically"
  },
  {
    icon: TrendingUp,
    title: "Multi-Platform",
    description: "Post to TikTok, Instagram, and YouTube"
  }
];

const testimonials = [
  {
    name: "Sarah M.",
    role: "Content Creator",
    content: "Went from 0 to 50K followers in 2 months using ViralPilot. The AI understands exactly what goes viral.",
    avatar: "S"
  },
  {
    name: "Mike T.",
    role: "True Crime Channel",
    content: "I run 5 channels now, all automated. Making $3K/month passive income.",
    avatar: "M"
  },
  {
    name: "Jessica L.",
    role: "Motivation Niche",
    content: "The caption styles are incredible. My engagement doubled overnight.",
    avatar: "J"
  }
];

const pricingPlans = [
  {
    name: "Hobby",
    price: 19,
    period: "month",
    description: "Best for creators starting with faceless content",
    features: [
      "3 times per week posting",
      "1 Series",
      "Automated posting",
      "Background music",
      "6+ video art styles",
      "Custom AI voiceover",
      "No watermark"
    ],
    cta: "Start Free Trial",
    popular: false
  },
  {
    name: "Daily",
    price: 39,
    period: "month",
    description: "Best for creators who want to grow fast",
    features: [
      "Posts every day",
      "3 Series",
      "Everything in Hobby",
      "Priority rendering",
      "All 25+ art styles",
      "Custom music upload",
      "Analytics dashboard"
    ],
    cta: "Start Free Trial",
    popular: true
  },
  {
    name: "Pro",
    price: 69,
    period: "month",
    description: "Best for creators who want to grow super fast",
    features: [
      "2 times per day posting",
      "10 Series",
      "Everything in Daily",
      "API access",
      "White-label videos",
      "Team members",
      "Priority support"
    ],
    cta: "Start Free Trial",
    popular: false
  }
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-lg border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Video className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">ViralPilot</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <Link href="#features" className="text-muted-foreground hover:text-foreground transition">Features</Link>
              <Link href="#pricing" className="text-muted-foreground hover:text-foreground transition">Pricing</Link>
              <Link href="#testimonials" className="text-muted-foreground hover:text-foreground transition">Testimonials</Link>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/sign-in">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link href="/sign-up">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full mb-6">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">Trusted by 50,000+ creators</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Create Viral Videos
              <br />
              <span className="gradient-text">On Autopilot</span>
            </h1>
            
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
              AI generates scripts, images, voiceovers, and captions. 
              Just pick your niche and watch your channels grow.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/sign-up">
                <Button size="lg" className="gap-2 text-lg px-8">
                  Start Creating Free
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="gap-2 text-lg px-8">
                <Play className="w-5 h-5" />
                Watch Demo
              </Button>
            </div>
            
            <p className="text-sm text-muted-foreground mt-4">
              No credit card required • 5 free videos
            </p>
          </motion.div>

          {/* Hero Video Preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-16 relative"
          >
            <div className="bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-orange-500/20 rounded-2xl p-1">
              <div className="bg-card rounded-xl overflow-hidden shadow-2xl">
                <div className="aspect-video bg-muted flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Play className="w-10 h-10 text-primary" />
                    </div>
                    <p className="text-muted-foreground">Dashboard Preview</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Floating badges */}
            <div className="absolute -left-4 top-1/4 bg-card border rounded-lg p-3 shadow-lg hidden lg:block">
              <div className="flex items-center gap-2">
                <Instagram className="w-5 h-5 text-pink-500" />
                <span className="text-sm font-medium">Auto-posted!</span>
              </div>
            </div>
            <div className="absolute -right-4 top-1/3 bg-card border rounded-lg p-3 shadow-lg hidden lg:block">
              <div className="flex items-center gap-2">
                <Youtube className="w-5 h-5 text-red-500" />
                <span className="text-sm font-medium">10K views</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-muted/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Everything You Need to Go Viral
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              From script to screen in minutes. No editing skills required.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
                className="bg-card border rounded-xl p-6 card-hover"
              >
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              How It Works
            </h2>
            <p className="text-xl text-muted-foreground">
              Three simple steps to automated content
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "1", title: "Choose Your Niche", desc: "True crime, horror, motivation, finance, and more" },
              { step: "2", title: "Customize Style", desc: "Pick art style, voice, captions, and music" },
              { step: "3", title: "Set & Forget", desc: "Schedule posts and watch your channels grow" }
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="w-16 h-16 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                <p className="text-muted-foreground">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 px-4 bg-muted/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Loved by Creators
            </h2>
            <p className="text-xl text-muted-foreground">
              Join thousands of successful content creators
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
                className="bg-card border rounded-xl p-6"
              >
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-yellow-500 text-yellow-500" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-4">"{t.content}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center font-semibold text-primary">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="font-semibold">{t.name}</p>
                    <p className="text-sm text-muted-foreground">{t.role}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-muted-foreground">
              Start free, upgrade when you're ready
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingPlans.map((plan, i) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
                className={`relative bg-card border rounded-xl p-6 ${
                  plan.popular ? "border-primary shadow-lg scale-105" : ""
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-sm font-medium px-3 py-1 rounded-full">
                    Most Popular
                  </div>
                )}
                <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold">${plan.price}</span>
                  <span className="text-muted-foreground">/{plan.period}</span>
                </div>
                <p className="text-sm text-muted-foreground mb-6">{plan.description}</p>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <Check className="w-5 h-5 text-primary" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button className="w-full" variant={plan.popular ? "default" : "outline"}>
                  {plan.cta}
                </Button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-orange-500/20 rounded-2xl p-12">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Ready to Go Viral?
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              Join 50,000+ creators automating their content. Start free today.
            </p>
            <Link href="/sign-up">
              <Button size="lg" className="gap-2 text-lg px-8">
                Start Creating Free
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Video className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">ViralPilot</span>
            </div>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <Link href="/privacy" className="hover:text-foreground transition">Privacy</Link>
              <Link href="/terms" className="hover:text-foreground transition">Terms</Link>
              <Link href="/support" className="hover:text-foreground transition">Support</Link>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2024 ViralPilot. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
