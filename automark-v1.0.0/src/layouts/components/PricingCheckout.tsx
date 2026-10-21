import React, { useState } from "react";

interface PricingCheckoutProps {
  planTitle: string;
  monthlyPrice: string;
  yearlyPrice: string;
  buttonLabel?: string;
  isFeatured?: boolean;
}

export default function PricingCheckout({
  planTitle,
  monthlyPrice,
  yearlyPrice,
  buttonLabel = "Get Access",
  isFeatured = false,
}: PricingCheckoutProps) {
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) {
      setError("Please enter your name and email.");
      return;
    }

    setLoading(true);
    setError("");

    // Determine interval dynamically directly from the DOM checkbox
    const toggleEl = document.getElementById("pricing-toggle") as HTMLInputElement;
    const isYearly = toggleEl?.checked ?? false;

    const priceToCharge = isYearly ? yearlyPrice : monthlyPrice;
    const intervalToCharge = isYearly ? "year" : "month";

    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email,
          planTitle,
          price: priceToCharge,
          interval: intervalToCharge,
        }),
      });

      const data = await res.json();
      if (data.success && data.url) {
        window.location.href = data.url;
      } else {
        setError(data.error || "Failed to initiate checkout. Please try again.");
        setLoading(false);
      }
    } catch (err: any) {
      setError("Network error occurred. Please try again.");
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => {
          if (monthlyPrice === "0" || parseFloat(monthlyPrice) === 0) {
            if (typeof window !== "undefined" && (window as any).MagicFillAuth?.openRegister) {
              (window as any).MagicFillAuth.openRegister();
            } else {
              const modal = document.getElementById("magicAuthModal");
              if (modal) {
                modal.classList.remove("hidden");
                modal.classList.add("flex");
              }
            }
          } else {
            setShowModal(true);
          }
        }}
        className={`${isFeatured ? "neu-btn-primary" : "neu-btn-secondary"} w-full py-3.5 my-8 block text-center cursor-pointer rounded-2xl text-xs font-bold uppercase tracking-wider`}
      >
        {buttonLabel}
      </button>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs px-4">
          <div className="bg-[#E0E5EC] p-8 rounded-[32px] w-full max-w-md neu-card relative">
            <button
              onClick={() => setShowModal(false)}
              className="neu-btn-secondary size-8 rounded-xl absolute top-6 right-6 flex items-center justify-center text-[#3D4852]"
              aria-label="Close"
            >
              &times;
            </button>
            <h3 className="text-xl font-bold font-display mb-2 text-[#3D4852]">
              Unlock {planTitle}
            </h3>
            <p className="text-xs font-body text-[#6B7280] mb-6">
              Enter your details below to activate your account credentials before checkout.
            </p>

            <form onSubmit={handleCheckout} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#3D4852] mb-1.5 font-display">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="neu-input w-full text-sm"
                  placeholder="John Doe"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-[#3D4852] mb-1.5 font-display">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="neu-input w-full text-sm"
                  placeholder="john@example.com"
                  disabled={loading}
                />
              </div>

              {error && <p className="text-rose-500 text-xs font-medium mt-2">{error}</p>}

              <button
                type="submit"
                disabled={loading}
                className="neu-btn-primary w-full py-3 rounded-2xl mt-6 flex justify-center items-center gap-2 text-xs font-bold uppercase tracking-wider disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  "Proceed to Payment"
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
