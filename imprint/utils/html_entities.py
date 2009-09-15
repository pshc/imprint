# -*- coding: utf-8 -*-
import re

# http://www.w3.org/TR/html4/sgml/entities.html
entity_spec = """
<!-- Portions © International Organization for Standardization 1986
     Permission to copy in any form is granted for use with
     conforming SGML systems and applications as defined in
     ISO 8879, provided this notice is included in all copies.
-->
<!-- Character entity set. Typical invocation:
     <!ENTITY % HTMLlat1 PUBLIC
       "-//W3C//ENTITIES Latin 1//EN//HTML">
     %HTMLlat1;
-->

<!ENTITY nbsp   CDATA "&#160;" -- no-break space = non-breaking space,
                                  U+00A0 ISOnum -->
<!ENTITY iexcl  CDATA "&#161;" -- inverted exclamation mark, U+00A1 ISOnum -->
<!ENTITY cent   CDATA "&#162;" -- cent sign, U+00A2 ISOnum -->
<!ENTITY pound  CDATA "&#163;" -- pound sign, U+00A3 ISOnum -->
<!ENTITY curren CDATA "&#164;" -- currency sign, U+00A4 ISOnum -->
<!ENTITY yen    CDATA "&#165;" -- yen sign = yuan sign, U+00A5 ISOnum -->
<!ENTITY brvbar CDATA "&#166;" -- broken bar = broken vertical bar,
                                  U+00A6 ISOnum -->
<!ENTITY sect   CDATA "&#167;" -- section sign, U+00A7 ISOnum -->
<!ENTITY uml    CDATA "&#168;" -- diaeresis = spacing diaeresis,
                                  U+00A8 ISOdia -->
<!ENTITY copy   CDATA "&#169;" -- copyright sign, U+00A9 ISOnum -->
<!ENTITY ordf   CDATA "&#170;" -- feminine ordinal indicator, U+00AA ISOnum -->
<!ENTITY laquo  CDATA "&#171;" -- left-pointing double angle quotation mark
                                  = left pointing guillemet, U+00AB ISOnum -->
<!ENTITY not    CDATA "&#172;" -- not sign, U+00AC ISOnum -->
<!ENTITY shy    CDATA "&#173;" -- soft hyphen = discretionary hyphen,
                                  U+00AD ISOnum -->
<!ENTITY reg    CDATA "&#174;" -- registered sign = registered trade mark sign,
                                  U+00AE ISOnum -->
<!ENTITY macr   CDATA "&#175;" -- macron = spacing macron = overline
                                  = APL overbar, U+00AF ISOdia -->
<!ENTITY deg    CDATA "&#176;" -- degree sign, U+00B0 ISOnum -->
<!ENTITY plusmn CDATA "&#177;" -- plus-minus sign = plus-or-minus sign,
                                  U+00B1 ISOnum -->
<!ENTITY sup2   CDATA "&#178;" -- superscript two = superscript digit two
                                  = squared, U+00B2 ISOnum -->
<!ENTITY sup3   CDATA "&#179;" -- superscript three = superscript digit three
                                  = cubed, U+00B3 ISOnum -->
<!ENTITY acute  CDATA "&#180;" -- acute accent = spacing acute,
                                  U+00B4 ISOdia -->
<!ENTITY micro  CDATA "&#181;" -- micro sign, U+00B5 ISOnum -->
<!ENTITY para   CDATA "&#182;" -- pilcrow sign = paragraph sign,
                                  U+00B6 ISOnum -->
<!ENTITY middot CDATA "&#183;" -- middle dot = Georgian comma
                                  = Greek middle dot, U+00B7 ISOnum -->
<!ENTITY cedil  CDATA "&#184;" -- cedilla = spacing cedilla, U+00B8 ISOdia -->
<!ENTITY sup1   CDATA "&#185;" -- superscript one = superscript digit one,
                                  U+00B9 ISOnum -->
<!ENTITY ordm   CDATA "&#186;" -- masculine ordinal indicator,
                                  U+00BA ISOnum -->
<!ENTITY raquo  CDATA "&#187;" -- right-pointing double angle quotation mark
                                  = right pointing guillemet, U+00BB ISOnum -->
<!ENTITY frac14 CDATA "&#188;" -- vulgar fraction one quarter
                                  = fraction one quarter, U+00BC ISOnum -->
<!ENTITY frac12 CDATA "&#189;" -- vulgar fraction one half
                                  = fraction one half, U+00BD ISOnum -->
<!ENTITY frac34 CDATA "&#190;" -- vulgar fraction three quarters
                                  = fraction three quarters, U+00BE ISOnum -->
<!ENTITY iquest CDATA "&#191;" -- inverted question mark
                                  = turned question mark, U+00BF ISOnum -->
<!ENTITY Agrave CDATA "&#192;" -- latin capital letter A with grave
                                  = latin capital letter A grave,
                                  U+00C0 ISOlat1 -->
<!ENTITY Aacute CDATA "&#193;" -- latin capital letter A with acute,
                                  U+00C1 ISOlat1 -->
<!ENTITY Acirc  CDATA "&#194;" -- latin capital letter A with circumflex,
                                  U+00C2 ISOlat1 -->
<!ENTITY Atilde CDATA "&#195;" -- latin capital letter A with tilde,
                                  U+00C3 ISOlat1 -->
<!ENTITY Auml   CDATA "&#196;" -- latin capital letter A with diaeresis,
                                  U+00C4 ISOlat1 -->
<!ENTITY Aring  CDATA "&#197;" -- latin capital letter A with ring above
                                  = latin capital letter A ring,
                                  U+00C5 ISOlat1 -->
<!ENTITY AElig  CDATA "&#198;" -- latin capital letter AE
                                  = latin capital ligature AE,
                                  U+00C6 ISOlat1 -->
<!ENTITY Ccedil CDATA "&#199;" -- latin capital letter C with cedilla,
                                  U+00C7 ISOlat1 -->
<!ENTITY Egrave CDATA "&#200;" -- latin capital letter E with grave,
                                  U+00C8 ISOlat1 -->
<!ENTITY Eacute CDATA "&#201;" -- latin capital letter E with acute,
                                  U+00C9 ISOlat1 -->
<!ENTITY Ecirc  CDATA "&#202;" -- latin capital letter E with circumflex,
                                  U+00CA ISOlat1 -->
<!ENTITY Euml   CDATA "&#203;" -- latin capital letter E with diaeresis,
                                  U+00CB ISOlat1 -->
<!ENTITY Igrave CDATA "&#204;" -- latin capital letter I with grave,
                                  U+00CC ISOlat1 -->
<!ENTITY Iacute CDATA "&#205;" -- latin capital letter I with acute,
                                  U+00CD ISOlat1 -->
<!ENTITY Icirc  CDATA "&#206;" -- latin capital letter I with circumflex,
                                  U+00CE ISOlat1 -->
<!ENTITY Iuml   CDATA "&#207;" -- latin capital letter I with diaeresis,
                                  U+00CF ISOlat1 -->
<!ENTITY ETH    CDATA "&#208;" -- latin capital letter ETH, U+00D0 ISOlat1 -->
<!ENTITY Ntilde CDATA "&#209;" -- latin capital letter N with tilde,
                                  U+00D1 ISOlat1 -->
<!ENTITY Ograve CDATA "&#210;" -- latin capital letter O with grave,
                                  U+00D2 ISOlat1 -->
<!ENTITY Oacute CDATA "&#211;" -- latin capital letter O with acute,
                                  U+00D3 ISOlat1 -->
<!ENTITY Ocirc  CDATA "&#212;" -- latin capital letter O with circumflex,
                                  U+00D4 ISOlat1 -->
<!ENTITY Otilde CDATA "&#213;" -- latin capital letter O with tilde,
                                  U+00D5 ISOlat1 -->
<!ENTITY Ouml   CDATA "&#214;" -- latin capital letter O with diaeresis,
                                  U+00D6 ISOlat1 -->
<!ENTITY times  CDATA "&#215;" -- multiplication sign, U+00D7 ISOnum -->
<!ENTITY Oslash CDATA "&#216;" -- latin capital letter O with stroke
                                  = latin capital letter O slash,
                                  U+00D8 ISOlat1 -->
<!ENTITY Ugrave CDATA "&#217;" -- latin capital letter U with grave,
                                  U+00D9 ISOlat1 -->
<!ENTITY Uacute CDATA "&#218;" -- latin capital letter U with acute,
                                  U+00DA ISOlat1 -->
<!ENTITY Ucirc  CDATA "&#219;" -- latin capital letter U with circumflex,
                                  U+00DB ISOlat1 -->
<!ENTITY Uuml   CDATA "&#220;" -- latin capital letter U with diaeresis,
                                  U+00DC ISOlat1 -->
<!ENTITY Yacute CDATA "&#221;" -- latin capital letter Y with acute,
                                  U+00DD ISOlat1 -->
<!ENTITY THORN  CDATA "&#222;" -- latin capital letter THORN,
                                  U+00DE ISOlat1 -->
<!ENTITY szlig  CDATA "&#223;" -- latin small letter sharp s = ess-zed,
                                  U+00DF ISOlat1 -->
<!ENTITY agrave CDATA "&#224;" -- latin small letter a with grave
                                  = latin small letter a grave,
                                  U+00E0 ISOlat1 -->
<!ENTITY aacute CDATA "&#225;" -- latin small letter a with acute,
                                  U+00E1 ISOlat1 -->
<!ENTITY acirc  CDATA "&#226;" -- latin small letter a with circumflex,
                                  U+00E2 ISOlat1 -->
<!ENTITY atilde CDATA "&#227;" -- latin small letter a with tilde,
                                  U+00E3 ISOlat1 -->
<!ENTITY auml   CDATA "&#228;" -- latin small letter a with diaeresis,
                                  U+00E4 ISOlat1 -->
<!ENTITY aring  CDATA "&#229;" -- latin small letter a with ring above
                                  = latin small letter a ring,
                                  U+00E5 ISOlat1 -->
<!ENTITY aelig  CDATA "&#230;" -- latin small letter ae
                                  = latin small ligature ae, U+00E6 ISOlat1 -->
<!ENTITY ccedil CDATA "&#231;" -- latin small letter c with cedilla,
                                  U+00E7 ISOlat1 -->
<!ENTITY egrave CDATA "&#232;" -- latin small letter e with grave,
                                  U+00E8 ISOlat1 -->
<!ENTITY eacute CDATA "&#233;" -- latin small letter e with acute,
                                  U+00E9 ISOlat1 -->
<!ENTITY ecirc  CDATA "&#234;" -- latin small letter e with circumflex,
                                  U+00EA ISOlat1 -->
<!ENTITY euml   CDATA "&#235;" -- latin small letter e with diaeresis,
                                  U+00EB ISOlat1 -->
<!ENTITY igrave CDATA "&#236;" -- latin small letter i with grave,
                                  U+00EC ISOlat1 -->
<!ENTITY iacute CDATA "&#237;" -- latin small letter i with acute,
                                  U+00ED ISOlat1 -->
<!ENTITY icirc  CDATA "&#238;" -- latin small letter i with circumflex,
                                  U+00EE ISOlat1 -->
<!ENTITY iuml   CDATA "&#239;" -- latin small letter i with diaeresis,
                                  U+00EF ISOlat1 -->
<!ENTITY eth    CDATA "&#240;" -- latin small letter eth, U+00F0 ISOlat1 -->
<!ENTITY ntilde CDATA "&#241;" -- latin small letter n with tilde,
                                  U+00F1 ISOlat1 -->
<!ENTITY ograve CDATA "&#242;" -- latin small letter o with grave,
                                  U+00F2 ISOlat1 -->
<!ENTITY oacute CDATA "&#243;" -- latin small letter o with acute,
                                  U+00F3 ISOlat1 -->
<!ENTITY ocirc  CDATA "&#244;" -- latin small letter o with circumflex,
                                  U+00F4 ISOlat1 -->
<!ENTITY otilde CDATA "&#245;" -- latin small letter o with tilde,
                                  U+00F5 ISOlat1 -->
<!ENTITY ouml   CDATA "&#246;" -- latin small letter o with diaeresis,
                                  U+00F6 ISOlat1 -->
<!ENTITY divide CDATA "&#247;" -- division sign, U+00F7 ISOnum -->
<!ENTITY oslash CDATA "&#248;" -- latin small letter o with stroke,
                                  = latin small letter o slash,
                                  U+00F8 ISOlat1 -->
<!ENTITY ugrave CDATA "&#249;" -- latin small letter u with grave,
                                  U+00F9 ISOlat1 -->
<!ENTITY uacute CDATA "&#250;" -- latin small letter u with acute,
                                  U+00FA ISOlat1 -->
<!ENTITY ucirc  CDATA "&#251;" -- latin small letter u with circumflex,
                                  U+00FB ISOlat1 -->
<!ENTITY uuml   CDATA "&#252;" -- latin small letter u with diaeresis,
                                  U+00FC ISOlat1 -->
<!ENTITY yacute CDATA "&#253;" -- latin small letter y with acute,
                                  U+00FD ISOlat1 -->
<!ENTITY thorn  CDATA "&#254;" -- latin small letter thorn,
                                  U+00FE ISOlat1 -->
<!ENTITY yuml   CDATA "&#255;" -- latin small letter y with diaeresis,
                                  U+00FF ISOlat1 -->

<!-- Mathematical, Greek and Symbolic characters for HTML -->

<!-- Character entity set. Typical invocation:
     <!ENTITY % HTMLsymbol PUBLIC
       "-//W3C//ENTITIES Symbols//EN//HTML">
     %HTMLsymbol; -->

<!-- Portions © International Organization for Standardization 1986:
     Permission to copy in any form is granted for use with
     conforming SGML systems and applications as defined in
     ISO 8879, provided this notice is included in all copies.
-->

<!-- Relevant ISO entity set is given unless names are newly introduced.
     New names (i.e., not in ISO 8879 list) do not clash with any
     existing ISO 8879 entity names. ISO 10646 character numbers
     are given for each character, in hex. CDATA values are decimal
     conversions of the ISO 10646 values and refer to the document
     character set. Names are ISO 10646 names. 

-->

<!-- Latin Extended-B -->
<!ENTITY fnof     CDATA "&#402;" -- latin small f with hook = function
                                    = florin, U+0192 ISOtech -->

<!-- Greek -->
<!ENTITY Alpha    CDATA "&#913;" -- greek capital letter alpha, U+0391 -->
<!ENTITY Beta     CDATA "&#914;" -- greek capital letter beta, U+0392 -->
<!ENTITY Gamma    CDATA "&#915;" -- greek capital letter gamma,
                                    U+0393 ISOgrk3 -->
<!ENTITY Delta    CDATA "&#916;" -- greek capital letter delta,
                                    U+0394 ISOgrk3 -->
<!ENTITY Epsilon  CDATA "&#917;" -- greek capital letter epsilon, U+0395 -->
<!ENTITY Zeta     CDATA "&#918;" -- greek capital letter zeta, U+0396 -->
<!ENTITY Eta      CDATA "&#919;" -- greek capital letter eta, U+0397 -->
<!ENTITY Theta    CDATA "&#920;" -- greek capital letter theta,
                                    U+0398 ISOgrk3 -->
<!ENTITY Iota     CDATA "&#921;" -- greek capital letter iota, U+0399 -->
<!ENTITY Kappa    CDATA "&#922;" -- greek capital letter kappa, U+039A -->
<!ENTITY Lambda   CDATA "&#923;" -- greek capital letter lambda,
                                    U+039B ISOgrk3 -->
<!ENTITY Mu       CDATA "&#924;" -- greek capital letter mu, U+039C -->
<!ENTITY Nu       CDATA "&#925;" -- greek capital letter nu, U+039D -->
<!ENTITY Xi       CDATA "&#926;" -- greek capital letter xi, U+039E ISOgrk3 -->
<!ENTITY Omicron  CDATA "&#927;" -- greek capital letter omicron, U+039F -->
<!ENTITY Pi       CDATA "&#928;" -- greek capital letter pi, U+03A0 ISOgrk3 -->
<!ENTITY Rho      CDATA "&#929;" -- greek capital letter rho, U+03A1 -->
<!-- there is no Sigmaf, and no U+03A2 character either -->
<!ENTITY Sigma    CDATA "&#931;" -- greek capital letter sigma,
                                    U+03A3 ISOgrk3 -->
<!ENTITY Tau      CDATA "&#932;" -- greek capital letter tau, U+03A4 -->
<!ENTITY Upsilon  CDATA "&#933;" -- greek capital letter upsilon,
                                    U+03A5 ISOgrk3 -->
<!ENTITY Phi      CDATA "&#934;" -- greek capital letter phi,
                                    U+03A6 ISOgrk3 -->
<!ENTITY Chi      CDATA "&#935;" -- greek capital letter chi, U+03A7 -->
<!ENTITY Psi      CDATA "&#936;" -- greek capital letter psi,
                                    U+03A8 ISOgrk3 -->
<!ENTITY Omega    CDATA "&#937;" -- greek capital letter omega,
                                    U+03A9 ISOgrk3 -->

<!ENTITY alpha    CDATA "&#945;" -- greek small letter alpha,
                                    U+03B1 ISOgrk3 -->
<!ENTITY beta     CDATA "&#946;" -- greek small letter beta, U+03B2 ISOgrk3 -->
<!ENTITY gamma    CDATA "&#947;" -- greek small letter gamma,
                                    U+03B3 ISOgrk3 -->
<!ENTITY delta    CDATA "&#948;" -- greek small letter delta,
                                    U+03B4 ISOgrk3 -->
<!ENTITY epsilon  CDATA "&#949;" -- greek small letter epsilon,
                                    U+03B5 ISOgrk3 -->
<!ENTITY zeta     CDATA "&#950;" -- greek small letter zeta, U+03B6 ISOgrk3 -->
<!ENTITY eta      CDATA "&#951;" -- greek small letter eta, U+03B7 ISOgrk3 -->
<!ENTITY theta    CDATA "&#952;" -- greek small letter theta,
                                    U+03B8 ISOgrk3 -->
<!ENTITY iota     CDATA "&#953;" -- greek small letter iota, U+03B9 ISOgrk3 -->
<!ENTITY kappa    CDATA "&#954;" -- greek small letter kappa,
                                    U+03BA ISOgrk3 -->
<!ENTITY lambda   CDATA "&#955;" -- greek small letter lambda,
                                    U+03BB ISOgrk3 -->
<!ENTITY mu       CDATA "&#956;" -- greek small letter mu, U+03BC ISOgrk3 -->
<!ENTITY nu       CDATA "&#957;" -- greek small letter nu, U+03BD ISOgrk3 -->
<!ENTITY xi       CDATA "&#958;" -- greek small letter xi, U+03BE ISOgrk3 -->
<!ENTITY omicron  CDATA "&#959;" -- greek small letter omicron, U+03BF NEW -->
<!ENTITY pi       CDATA "&#960;" -- greek small letter pi, U+03C0 ISOgrk3 -->
<!ENTITY rho      CDATA "&#961;" -- greek small letter rho, U+03C1 ISOgrk3 -->
<!ENTITY sigmaf   CDATA "&#962;" -- greek small letter final sigma,
                                    U+03C2 ISOgrk3 -->
<!ENTITY sigma    CDATA "&#963;" -- greek small letter sigma,
                                    U+03C3 ISOgrk3 -->
<!ENTITY tau      CDATA "&#964;" -- greek small letter tau, U+03C4 ISOgrk3 -->
<!ENTITY upsilon  CDATA "&#965;" -- greek small letter upsilon,
                                    U+03C5 ISOgrk3 -->
<!ENTITY phi      CDATA "&#966;" -- greek small letter phi, U+03C6 ISOgrk3 -->
<!ENTITY chi      CDATA "&#967;" -- greek small letter chi, U+03C7 ISOgrk3 -->
<!ENTITY psi      CDATA "&#968;" -- greek small letter psi, U+03C8 ISOgrk3 -->
<!ENTITY omega    CDATA "&#969;" -- greek small letter omega,
                                    U+03C9 ISOgrk3 -->
<!ENTITY thetasym CDATA "&#977;" -- greek small letter theta symbol,
                                    U+03D1 NEW -->
<!ENTITY upsih    CDATA "&#978;" -- greek upsilon with hook symbol,
                                    U+03D2 NEW -->
<!ENTITY piv      CDATA "&#982;" -- greek pi symbol, U+03D6 ISOgrk3 -->

<!-- General Punctuation -->
<!ENTITY bull     CDATA "&#8226;" -- bullet = black small circle,
                                     U+2022 ISOpub  -->
<!-- bullet is NOT the same as bullet operator, U+2219 -->
<!ENTITY hellip   CDATA "&#8230;" -- horizontal ellipsis = three dot leader,
                                     U+2026 ISOpub  -->
<!ENTITY prime    CDATA "&#8242;" -- prime = minutes = feet, U+2032 ISOtech -->
<!ENTITY Prime    CDATA "&#8243;" -- double prime = seconds = inches,
                                     U+2033 ISOtech -->
<!ENTITY oline    CDATA "&#8254;" -- overline = spacing overscore,
                                     U+203E NEW -->
<!ENTITY frasl    CDATA "&#8260;" -- fraction slash, U+2044 NEW -->

<!-- Letterlike Symbols -->
<!ENTITY weierp   CDATA "&#8472;" -- script capital P = power set
                                     = Weierstrass p, U+2118 ISOamso -->
<!ENTITY image    CDATA "&#8465;" -- blackletter capital I = imaginary part,
                                     U+2111 ISOamso -->
<!ENTITY real     CDATA "&#8476;" -- blackletter capital R = real part symbol,
                                     U+211C ISOamso -->
<!ENTITY trade    CDATA "&#8482;" -- trade mark sign, U+2122 ISOnum -->
<!ENTITY alefsym  CDATA "&#8501;" -- alef symbol = first transfinite cardinal,
                                     U+2135 NEW -->
<!-- alef symbol is NOT the same as hebrew letter alef,
     U+05D0 although the same glyph could be used to depict both characters -->

<!-- Arrows -->
<!ENTITY larr     CDATA "&#8592;" -- leftwards arrow, U+2190 ISOnum -->
<!ENTITY uarr     CDATA "&#8593;" -- upwards arrow, U+2191 ISOnum-->
<!ENTITY rarr     CDATA "&#8594;" -- rightwards arrow, U+2192 ISOnum -->
<!ENTITY darr     CDATA "&#8595;" -- downwards arrow, U+2193 ISOnum -->
<!ENTITY harr     CDATA "&#8596;" -- left right arrow, U+2194 ISOamsa -->
<!ENTITY crarr    CDATA "&#8629;" -- downwards arrow with corner leftwards
                                     = carriage return, U+21B5 NEW -->
<!ENTITY lArr     CDATA "&#8656;" -- leftwards double arrow, U+21D0 ISOtech -->
<!-- ISO 10646 does not say that lArr is the same as the 'is implied by' arrow
    but also does not have any other character for that function. So ? lArr can
    be used for 'is implied by' as ISOtech suggests -->
<!ENTITY uArr     CDATA "&#8657;" -- upwards double arrow, U+21D1 ISOamsa -->
<!ENTITY rArr     CDATA "&#8658;" -- rightwards double arrow,
                                     U+21D2 ISOtech -->
<!-- ISO 10646 does not say this is the 'implies' character but does not have 
     another character with this function so ?
     rArr can be used for 'implies' as ISOtech suggests -->
<!ENTITY dArr     CDATA "&#8659;" -- downwards double arrow, U+21D3 ISOamsa -->
<!ENTITY hArr     CDATA "&#8660;" -- left right double arrow,
                                     U+21D4 ISOamsa -->

<!-- Mathematical Operators -->
<!ENTITY forall   CDATA "&#8704;" -- for all, U+2200 ISOtech -->
<!ENTITY part     CDATA "&#8706;" -- partial differential, U+2202 ISOtech  -->
<!ENTITY exist    CDATA "&#8707;" -- there exists, U+2203 ISOtech -->
<!ENTITY empty    CDATA "&#8709;" -- empty set = null set = diameter,
                                     U+2205 ISOamso -->
<!ENTITY nabla    CDATA "&#8711;" -- nabla = backward difference,
                                     U+2207 ISOtech -->
<!ENTITY isin     CDATA "&#8712;" -- element of, U+2208 ISOtech -->
<!ENTITY notin    CDATA "&#8713;" -- not an element of, U+2209 ISOtech -->
<!ENTITY ni       CDATA "&#8715;" -- contains as member, U+220B ISOtech -->
<!-- should there be a more memorable name than 'ni'? -->
<!ENTITY prod     CDATA "&#8719;" -- n-ary product = product sign,
                                     U+220F ISOamsb -->
<!-- prod is NOT the same character as U+03A0 'greek capital letter pi' though
     the same glyph might be used for both -->
<!ENTITY sum      CDATA "&#8721;" -- n-ary sumation, U+2211 ISOamsb -->
<!-- sum is NOT the same character as U+03A3 'greek capital letter sigma'
     though the same glyph might be used for both -->
<!ENTITY minus    CDATA "&#8722;" -- minus sign, U+2212 ISOtech -->
<!ENTITY lowast   CDATA "&#8727;" -- asterisk operator, U+2217 ISOtech -->
<!ENTITY radic    CDATA "&#8730;" -- square root = radical sign,
                                     U+221A ISOtech -->
<!ENTITY prop     CDATA "&#8733;" -- proportional to, U+221D ISOtech -->
<!ENTITY infin    CDATA "&#8734;" -- infinity, U+221E ISOtech -->
<!ENTITY ang      CDATA "&#8736;" -- angle, U+2220 ISOamso -->
<!ENTITY and      CDATA "&#8743;" -- logical and = wedge, U+2227 ISOtech -->
<!ENTITY or       CDATA "&#8744;" -- logical or = vee, U+2228 ISOtech -->
<!ENTITY cap      CDATA "&#8745;" -- intersection = cap, U+2229 ISOtech -->
<!ENTITY cup      CDATA "&#8746;" -- union = cup, U+222A ISOtech -->
<!ENTITY int      CDATA "&#8747;" -- integral, U+222B ISOtech -->
<!ENTITY there4   CDATA "&#8756;" -- therefore, U+2234 ISOtech -->
<!ENTITY sim      CDATA "&#8764;" -- tilde operator = varies with = similar to,
                                     U+223C ISOtech -->
<!-- tilde operator is NOT the same character as the tilde, U+007E,
     although the same glyph might be used to represent both  -->
<!ENTITY cong     CDATA "&#8773;" -- approximately equal to, U+2245 ISOtech -->
<!ENTITY asymp    CDATA "&#8776;" -- almost equal to = asymptotic to,
                                     U+2248 ISOamsr -->
<!ENTITY ne       CDATA "&#8800;" -- not equal to, U+2260 ISOtech -->
<!ENTITY equiv    CDATA "&#8801;" -- identical to, U+2261 ISOtech -->
<!ENTITY le       CDATA "&#8804;" -- less-than or equal to, U+2264 ISOtech -->
<!ENTITY ge       CDATA "&#8805;" -- greater-than or equal to,
                                     U+2265 ISOtech -->
<!ENTITY sub      CDATA "&#8834;" -- subset of, U+2282 ISOtech -->
<!ENTITY sup      CDATA "&#8835;" -- superset of, U+2283 ISOtech -->
<!-- note that nsup, 'not a superset of, U+2283' is not covered by the Symbol 
     font encoding and is not included. Should it be, for symmetry?
     It is in ISOamsn  --> 
<!ENTITY nsub     CDATA "&#8836;" -- not a subset of, U+2284 ISOamsn -->
<!ENTITY sube     CDATA "&#8838;" -- subset of or equal to, U+2286 ISOtech -->
<!ENTITY supe     CDATA "&#8839;" -- superset of or equal to,
                                     U+2287 ISOtech -->
<!ENTITY oplus    CDATA "&#8853;" -- circled plus = direct sum,
                                     U+2295 ISOamsb -->
<!ENTITY otimes   CDATA "&#8855;" -- circled times = vector product,
                                     U+2297 ISOamsb -->
<!ENTITY perp     CDATA "&#8869;" -- up tack = orthogonal to = perpendicular,
                                     U+22A5 ISOtech -->
<!ENTITY sdot     CDATA "&#8901;" -- dot operator, U+22C5 ISOamsb -->
<!-- dot operator is NOT the same character as U+00B7 middle dot -->

<!-- Miscellaneous Technical -->
<!ENTITY lceil    CDATA "&#8968;" -- left ceiling = apl upstile,
                                     U+2308 ISOamsc  -->
<!ENTITY rceil    CDATA "&#8969;" -- right ceiling, U+2309 ISOamsc  -->
<!ENTITY lfloor   CDATA "&#8970;" -- left floor = apl downstile,
                                     U+230A ISOamsc  -->
<!ENTITY rfloor   CDATA "&#8971;" -- right floor, U+230B ISOamsc  -->
<!ENTITY lang     CDATA "&#9001;" -- left-pointing angle bracket = bra,
                                     U+2329 ISOtech -->
<!-- lang is NOT the same character as U+003C 'less than' 
     or U+2039 'single left-pointing angle quotation mark' -->
<!ENTITY rang     CDATA "&#9002;" -- right-pointing angle bracket = ket,
                                     U+232A ISOtech -->
<!-- rang is NOT the same character as U+003E 'greater than' 
     or U+203A 'single right-pointing angle quotation mark' -->

<!-- Geometric Shapes -->
<!ENTITY loz      CDATA "&#9674;" -- lozenge, U+25CA ISOpub -->

<!-- Miscellaneous Symbols -->
<!ENTITY spades   CDATA "&#9824;" -- black spade suit, U+2660 ISOpub -->
<!-- black here seems to mean filled as opposed to hollow -->
<!ENTITY clubs    CDATA "&#9827;" -- black club suit = shamrock,
                                     U+2663 ISOpub -->
<!ENTITY hearts   CDATA "&#9829;" -- black heart suit = valentine,
                                     U+2665 ISOpub -->
<!ENTITY diams    CDATA "&#9830;" -- black diamond suit, U+2666 ISOpub -->

<!-- Special characters for HTML -->

<!-- Character entity set. Typical invocation:
     <!ENTITY % HTMLspecial PUBLIC
       "-//W3C//ENTITIES Special//EN//HTML">
     %HTMLspecial; -->

<!-- Portions © International Organization for Standardization 1986:
     Permission to copy in any form is granted for use with
     conforming SGML systems and applications as defined in
     ISO 8879, provided this notice is included in all copies.
-->

<!-- Relevant ISO entity set is given unless names are newly introduced.
     New names (i.e., not in ISO 8879 list) do not clash with any
     existing ISO 8879 entity names. ISO 10646 character numbers
     are given for each character, in hex. CDATA values are decimal
     conversions of the ISO 10646 values and refer to the document
     character set. Names are ISO 10646 names. 

-->

<!-- C0 Controls and Basic Latin -->
<!ENTITY quot    CDATA "&#34;"   -- quotation mark = APL quote,
                                    U+0022 ISOnum -->
<!ENTITY amp     CDATA "&#38;"   -- ampersand, U+0026 ISOnum -->
<!ENTITY lt      CDATA "&#60;"   -- less-than sign, U+003C ISOnum -->
<!ENTITY gt      CDATA "&#62;"   -- greater-than sign, U+003E ISOnum -->

<!-- Latin Extended-A -->
<!ENTITY OElig   CDATA "&#338;"  -- latin capital ligature OE,
                                    U+0152 ISOlat2 -->
<!ENTITY oelig   CDATA "&#339;"  -- latin small ligature oe, U+0153 ISOlat2 -->
<!-- ligature is a misnomer, this is a separate character in some languages -->
<!ENTITY Scaron  CDATA "&#352;"  -- latin capital letter S with caron,
                                    U+0160 ISOlat2 -->
<!ENTITY scaron  CDATA "&#353;"  -- latin small letter s with caron,
                                    U+0161 ISOlat2 -->
<!ENTITY Yuml    CDATA "&#376;"  -- latin capital letter Y with diaeresis,
                                    U+0178 ISOlat2 -->

<!-- Spacing Modifier Letters -->
<!ENTITY circ    CDATA "&#710;"  -- modifier letter circumflex accent,
                                    U+02C6 ISOpub -->
<!ENTITY tilde   CDATA "&#732;"  -- small tilde, U+02DC ISOdia -->

<!-- General Punctuation -->
<!ENTITY ensp    CDATA "&#8194;" -- en space, U+2002 ISOpub -->
<!ENTITY emsp    CDATA "&#8195;" -- em space, U+2003 ISOpub -->
<!ENTITY thinsp  CDATA "&#8201;" -- thin space, U+2009 ISOpub -->
<!ENTITY zwnj    CDATA "&#8204;" -- zero width non-joiner,
                                    U+200C NEW RFC 2070 -->
<!ENTITY zwj     CDATA "&#8205;" -- zero width joiner, U+200D NEW RFC 2070 -->
<!ENTITY lrm     CDATA "&#8206;" -- left-to-right mark, U+200E NEW RFC 2070 -->
<!ENTITY rlm     CDATA "&#8207;" -- right-to-left mark, U+200F NEW RFC 2070 -->
<!ENTITY ndash   CDATA "&#8211;" -- en dash, U+2013 ISOpub -->
<!ENTITY mdash   CDATA "&#8212;" -- em dash, U+2014 ISOpub -->
<!ENTITY lsquo   CDATA "&#8216;" -- left single quotation mark,
                                    U+2018 ISOnum -->
<!ENTITY rsquo   CDATA "&#8217;" -- right single quotation mark,
                                    U+2019 ISOnum -->
<!ENTITY sbquo   CDATA "&#8218;" -- single low-9 quotation mark, U+201A NEW -->
<!ENTITY ldquo   CDATA "&#8220;" -- left double quotation mark,
                                    U+201C ISOnum -->
<!ENTITY rdquo   CDATA "&#8221;" -- right double quotation mark,
                                    U+201D ISOnum -->
<!ENTITY bdquo   CDATA "&#8222;" -- double low-9 quotation mark, U+201E NEW -->
<!ENTITY dagger  CDATA "&#8224;" -- dagger, U+2020 ISOpub -->
<!ENTITY Dagger  CDATA "&#8225;" -- double dagger, U+2021 ISOpub -->
<!ENTITY permil  CDATA "&#8240;" -- per mille sign, U+2030 ISOtech -->
<!ENTITY lsaquo  CDATA "&#8249;" -- single left-pointing angle quotation mark,
                                    U+2039 ISO proposed -->
<!-- lsaquo is proposed but not yet ISO standardized -->
<!ENTITY rsaquo  CDATA "&#8250;" -- single right-pointing angle quotation mark,
                                    U+203A ISO proposed -->
<!-- rsaquo is proposed but not yet ISO standardized -->
<!ENTITY euro   CDATA "&#8364;"  -- euro sign, U+20AC NEW -->
"""

entities = re.findall(r'<!ENTITY\s+(\w+)\s+CDATA\s+"&#(\d+);"', entity_spec)
#entities = filter(lambda e: e[0] not in ['quot', 'amp', 'lt', 'gt'], entities)
entities = dict((k, int(v)) for (k, v) in entities)
del entity_spec

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
