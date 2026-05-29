import { useState } from "react";
import { Input } from "./ui/input";
import { Phone } from "lucide-react";

const COUNTRIES = [
  { code: "RS", name: "Srbija", prefix: "+381" },
  { code: "HR", name: "Hrvatska", prefix: "+385" },
  { code: "BA", name: "Bosna i H.", prefix: "+387" },
  { code: "ME", name: "Crna Gora", prefix: "+382" },
  { code: "MK", name: "S. Makedonija", prefix: "+389" },
  { code: "SI", name: "Slovenija", prefix: "+386" },
  { code: "DE", name: "Nemačka", prefix: "+49" },
  { code: "AT", name: "Austrija", prefix: "+43" },
  { code: "CH", name: "Švajcarska", prefix: "+41" },
  { code: "IT", name: "Italija", prefix: "+39" },
  { code: "FR", name: "Francuska", prefix: "+33" },
  { code: "GB", name: "UK", prefix: "+44" },
  { code: "US", name: "SAD", prefix: "+1" },
  { code: "SE", name: "Švedska", prefix: "+46" },
  { code: "NO", name: "Norveška", prefix: "+47" },
];

const detectCountryFromValue = (value) => {
  if (!value) return COUNTRIES[0];
  const clean = value.replace(/\s/g, "");
  const match = COUNTRIES.find(c => clean.startsWith(c.prefix));
  return match || COUNTRIES[0];
};

const extractLocalNumber = (value, prefix) => {
  if (!value) return "";
  let clean = value.replace(/\s/g, "");
  if (clean.startsWith(prefix)) {
    clean = clean.substring(prefix.length);
  } else {
    clean = clean.replace(/^\+?\d{1,3}/, "");
  }
  clean = clean.replace(/\D/g, "");
  if (clean.startsWith("0")) clean = clean.substring(1);
  return clean;
};

export const PhoneInput = ({
  value,
  onChange,
  placeholder,
  className = "",
  "data-testid": testId = "phone-input",
}) => {
  const detected = detectCountryFromValue(value);
  const [country, setCountry] = useState(detected);
  const localNum = extractLocalNumber(value, country.prefix);

  const handleCountryChange = (e) => {
    const c = COUNTRIES.find(cc => cc.code === e.target.value) || COUNTRIES[0];
    setCountry(c);
    onChange(localNum ? `${c.prefix}${localNum}` : c.prefix);
  };

  const handleNumberChange = (e) => {
    let digits = e.target.value.replace(/\D/g, "");
    if (digits.startsWith("0")) digits = digits.substring(1);
    if (digits.length > 12) digits = digits.substring(0, 12);
    onChange(digits ? `${country.prefix}${digits}` : "");
  };

  return (
    <div className={`flex gap-2 ${className}`}>
      <select
        value={country.code}
        onChange={handleCountryChange}
        className="bg-[#141416] border border-[#2A2A2D] rounded-lg px-2 text-sm text-white min-h-[48px] w-[140px] flex-shrink-0 focus:border-[#C5A880] outline-none"
        data-testid={`${testId}-country`}
      >
        {COUNTRIES.map(c => (
          <option key={c.code} value={c.code}>
            {c.name} ({c.prefix})
          </option>
        ))}
      </select>
      <div className="relative flex-1">
        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
        <Input
          value={localNum}
          onChange={handleNumberChange}
          placeholder={placeholder || "641234567"}
          inputMode="tel"
          className="pl-10 bg-[#141416] border-[#2A2A2D] focus:border-[#C5A880] min-h-[48px] font-mono tracking-wide"
          data-testid={testId}
        />
      </div>
    </div>
  );
};

export const isValidPhone = (value) => {
  if (!value) return false;
  const match = COUNTRIES.find(c => value.startsWith(c.prefix));
  if (!match) return false;
  const local = value.substring(match.prefix.length);
  return /^\d{6,12}$/.test(local);
};

export default PhoneInput;
