import Link from "next/link";
import { Briefcase, Search, Bell, Bookmark, Zap, ArrowRight } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="bg-white">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-orange-50 to-white" />
        <div className="relative max-w-5xl mx-auto px-4 pt-20 pb-24 text-center">
          <div className="inline-flex items-center gap-2 bg-orange-100 text-hn px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Zap size={14} />
            Powered by AI parsing
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold text-gray-900 tracking-tight mb-6">
            Every HN Job.
            <br />
            <span className="text-hn">Structured & Searchable.</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            We scrape Hacker News &quot;Who&apos;s Hiring&quot; threads monthly, parse every
            listing with AI, and let you search, filter, and track jobs that
            match your skills.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="btn-primary text-lg px-8 py-3 flex items-center justify-center gap-2"
            >
              Browse Jobs
              <ArrowRight size={20} />
            </Link>
            <Link
              href="/auth/signup"
              className="btn-secondary text-lg px-8 py-3"
            >
              Create Account
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Everything you need to find your next role
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          <FeatureCard
            icon={<Search size={24} />}
            title="Smart Search"
            description="Full-text search across companies, roles, skills, and descriptions. Filter by remote, salary, visa, and more."
          />
          <FeatureCard
            icon={<Zap size={24} />}
            title="AI Match Score"
            description="Set your preferences and get a personalized match score for every listing. See why jobs score high or low."
          />
          <FeatureCard
            icon={<Bookmark size={24} />}
            title="Track Applications"
            description="Save jobs, track your application status from saved to offer, and add personal notes."
          />
          <FeatureCard
            icon={<Bell size={24} />}
            title="Email Alerts"
            description="Get weekly or daily digests of your top-matched jobs from the latest hiring thread."
          />
        </div>
      </section>

      {/* How it works */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            How it works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Step
              number={1}
              title="We scrape HN"
              description="On the 1st of each month, we automatically pull every comment from the latest 'Who's Hiring' thread."
            />
            <Step
              number={2}
              title="AI parses listings"
              description="GPT-4o-mini extracts company, role, salary, skills, location, and more from raw comments into structured data."
            />
            <Step
              number={3}
              title="You search & apply"
              description="Browse, filter, save, and track. Set up preferences to get a match score and email alerts for new postings."
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-4 py-20 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Ready to find your next opportunity?
        </h2>
        <p className="text-lg text-gray-600 mb-8">
          No spam, no recruiter noise. Just real jobs from the HN community.
        </p>
        <Link
          href="/dashboard"
          className="btn-primary text-lg px-8 py-3 inline-flex items-center gap-2"
        >
          <Briefcase size={20} />
          Start Browsing
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8">
        <div className="max-w-5xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-hn rounded flex items-center justify-center">
              <span className="text-white font-bold text-xs">HN</span>
            </div>
            <span>HN Jobs</span>
          </div>
          <p>
            Data sourced from{" "}
            <a
              href="https://news.ycombinator.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-hn hover:underline"
            >
              Hacker News
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 bg-orange-100 text-hn rounded-xl flex items-center justify-center mx-auto mb-4">
        {icon}
      </div>
      <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}

function Step({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <div className="text-center">
      <div className="w-10 h-10 bg-hn text-white rounded-full flex items-center justify-center mx-auto mb-4 font-bold">
        {number}
      </div>
      <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}
