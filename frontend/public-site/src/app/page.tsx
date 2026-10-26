import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { Architecture } from "@/components/Architecture";
import { Pricing } from "@/components/Pricing";
import { Metrics } from "@/components/Metrics";
import { Cta } from "@/components/Cta";

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      "name": "GymClubNex",
      "applicationCategory": "BusinessApplication",
      "operatingSystem": "Web, Cloud",
      "description":
        "Yeni nesil spor kulüpleri, stüdyolar ve tesis zincirleri için Fitness Network İşletim Sistemi.",
      "url": "https://gymclubnex.com",
      "offers": {
        "@type": "AggregateOffer",
        "priceCurrency": "TRY",
        "lowPrice": "0",
        "offerCount": "3",
      },
    },
    {
      "@type": "Organization",
      "name": "GymClubNex",
      "url": "https://gymclubnex.com",
      "email": "hello@gymclubnex.com",
      "logo": "https://gymclubnex.com/favicon.ico",
    },
  ],
};

export default function Home() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Hero />
      <Features />
      <Architecture />
      <Pricing />
      <Metrics />
      <Cta />
    </>
  );
}
