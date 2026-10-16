/* Matisse's Montparnasse — all station content in one place. Edit here, never in app.js.
   Coordinates are [lon, lat]. Panel framings default to a 2 × 3 page with 2.5% margins. */
window.WALK = {
  title: "Matisse's Montparnasse",
  date: "Wednesday 21 October 2026",
  hotel: { name: "Drawing House", coord: [2.319941, 48.837350] },
  defaultFrames: [
    { x: 0.025, y: 0.020, w: 0.46, h: 0.30 }, { x: 0.515, y: 0.020, w: 0.46, h: 0.30 },
    { x: 0.025, y: 0.350, w: 0.46, h: 0.30 }, { x: 0.515, y: 0.350, w: 0.46, h: 0.30 },
    { x: 0.025, y: 0.680, w: 0.46, h: 0.30 }, { x: 0.515, y: 0.680, w: 0.46, h: 0.30 }
  ],
  stations: [
    {
      id: "intro", n: 0, sticker: "house", accent: "#1F3A93", accentInk: "#FAF6EE",
      title: "Matisse in sixty seconds", place: "Drawing House, 21 rue Vercingétorix", time: "17:45",
      coord: [2.319941, 48.837350],
      audio: "audio/ep-00.mp3", audioLabel: "Who was Matisse? · 5 min",
      panels: "comic/panels-00.jpg",
      captions: [
        "Around 1890. Henri Matisse, a lawyer's clerk of about twenty, in bed after appendicitis. “A sort of paradise.”",
        "Paris, poor years. He buys a small Cézanne he cannot afford and keeps it 37 years.",
        "1905. A critic calls his colours “wild beasts”. Matisse looks like a professor.",
        "1908. He opens the Académie Matisse: a hundred students, nearly all foreigners.",
        "1941, aged 71. A cancer operation. Matisse asks the surgeon for three or four years.",
        "He gets thirteen, and invents a new art: drawing with scissors."
      ],
      then: { src: "art/matisse-self-portrait-1906.jpg", credit: "Henri Matisse, Self-portrait in a striped T-shirt, 1906. SMK Copenhagen. Public domain." },
      more: [
        { src: "art/woman-with-a-hat.jpg", credit: "Woman with a Hat, 1905. SFMOMA." },
        { src: "art/dance-1910.jpg", credit: "Dance, 1910. Hermitage." },
        { src: "art/red-studio-1911.jpg", credit: "The Red Studio, 1911. MoMA." }
      ],
      story: "Henri Matisse (1869–1954) came late to painting. A lawyer's clerk given a paint box in bed; the wild beasts of 1905; a school in 1908; Nice for the light; and after a cancer operation at 71, thirteen bonus years spent drawing with scissors.",
      fact: "The leader of the wild beasts wore gold-rimmed spectacles and a neat trimmed beard. A writer said you would take him for a professor or a doctor.",
      quiz: { q: "What did Matisse draw with in his last years?", a: "Scissors." }
    },
    {
      id: "gauguin", n: 1, sticker: "window", accent: "#2E7D4F", accentInk: "#FAF6EE",
      title: "Gauguin's street", place: "6 rue Vercingétorix", time: "17:50", leg: "then 700 m along avenue du Maine",
      coord: [2.321818, 48.838245],
      audio: "audio/ep-01.mp3", audioLabel: "The yellow studio · 4 min",
      panels: "comic/panels-01.jpg",
      captions: [
        "January 1894. Paul Gauguin, back from Tahiti, rents a top-floor studio at number 6.",
        "He paints the walls bright yellow and hangs them with Tahiti, four Van Goghs and a Cézanne.",
        "Every Thursday, an open evening: Mallarmé, Strindberg, Ravel, Delius, and the dealer Vollard.",
        "February 1894. Snow. Gauguin puts his easel at the window and paints the courtyard.",
        "July 1895. He leaves for Tahiti for good. The house is gone; the street was rebuilt.",
        "1899. Vollard sells the young Matisse a small Cézanne he cannot afford."
      ],
      then: { src: "art/gauguin-paris-in-the-snow-1894.jpg", credit: "Paul Gauguin, Paris in the Snow, 1894, painted from his window on this street. Van Gogh Museum. Public domain." },
      more: [ { src: "art/signac-rue-vercingetorix-1885.jpg", credit: "Paul Signac, Rue Vercingétorix, 1885. Louvre. Public domain." } ],
      stand: "Nothing from 1894 survives on this street; the painting is the view from a top-floor window here.",
      story: "Gauguin lived at number 6 from January 1894 to July 1895, in a studio painted bright yellow and hung with Tahiti, four Van Goghs and a Cézanne. Thursday evenings: Degas, Mallarmé, Strindberg, Ravel, and the dealer Vollard, who in 1899 sold the penniless Matisse a small Cézanne he kept for thirty-seven years.",
      fact: "The composer of Boléro came to Gauguin's parties on this street.",
      quiz: { q: "Which composer, famous for Boléro, came to Gauguin's Thursdays here?", a: "Maurice Ravel." }
    },
    {
      id: "canteen", n: 2, sticker: "bowl", accent: "#E63312", accentInk: "#FAF6EE",
      title: "The artists' canteen", place: "21 avenue du Maine", time: "18:07", leg: "then 400 m to the station square",
      coord: [2.320739, 48.843459],
      audio: "audio/ep-02.mp3", audioLabel: "Sixty-five centimes and no curfew · 4 min",
      panels: "comic/panels-02.jpg",
      captions: [
        "February 1915. War. Marie Vassilieff turns her studio into a canteen for artists.",
        "Broth, meat, vegetables, dessert, coffee: 65 centimes. Wine, 10 more.",
        "Registered as a private club, not a restaurant, so the curfew did not apply.",
        "January 1917. A banquet for Braque, back from the front. Modigliani is not invited.",
        "Modigliani comes anyway, drunk, and then a pistol appears. “Out!”",
        "All five feet of Marie push him down the stairs while Picasso holds the door."
      ],
      then: { src: "art/modigliani-marie-vassilieff.jpg", credit: "Amedeo Modigliani, Portrait of Marie Vassilieff, c. 1918. Public domain." },
      more: [ { src: "art/villa-vassilieff-alley-2016.jpg", credit: "The alley today, Villa Marie-Vassilieff. Photo Guilhem Vellut, 2016, CC BY 2.0." } ],
      stand: "Stand at the gate of the cobbled alley. The studio at the end is empty this autumn, between tenants.",
      story: "Marie Vassilieff, Russian, five feet tall, a student of Matisse's school, turned her studio into a canteen in February 1915: a full meal for sixty-five centimes, wine ten more, and no curfew, because on paper it was a club. In 1917 she threw a drunk Modigliani down the stairs.",
      fact: "She made portrait dolls of her famous friends, shown at the couturier Poiret's in 1916. One doll was Picasso.",
      quiz: { q: "Why could the canteen keep serving after the wartime curfew?", a: "It was registered as a private club, not a restaurant." }
    },
    {
      id: "station", n: 3, sticker: "hat", accent: "#1F3A93", accentInk: "#FAF6EE",
      title: "The old station and the Americans", place: "Place du 18-Juin-1940", time: "18:20", leg: "then 500 m east along the boulevard",
      coord: [2.324140, 48.844166],
      audio: "audio/ep-03.mp3", audioLabel: "The Swedes and the four hundred francs · 4 min",
      panels: "comic/panels-03.jpg",
      captions: [
        "October 1905. The Salon d'Automne. One room is full of violent colour. “Wild beasts!”",
        "Matisse's Woman with a Hat: colours nobody has seen on a face.",
        "Leo Stein, an American collector, stops in front of it. “The nastiest smear of paint I ever saw.”",
        "He comes back. And back. He wants it.",
        "Matisse asks 500 francs. Refuses 300. Writes: not under 450.",
        "Leo pays 400. Twenty per cent off the painting that started modern art."
      ],
      then: { src: "art/marquet-gare-montparnasse-1912.jpg", credit: "Albert Marquet, La Gare Montparnasse, 1912. The station stood on this square until the 1960s. Public domain." },
      more: [
        { src: "art/steins-studio-wall-1906.jpg", credit: "The Steins' studio, 27 rue de Fleurus, c. 1906; Woman with a Hat hangs top centre. Public domain." },
        { src: "art/souza-cardoso-brasserie-dumesnil.jpg", credit: "Amadeo de Souza-Cardoso, Brasserie Dumesnil, c. 1908–10, a café by this square. Photo Pedro Ribeiro Simões, CC BY 2.0." }
      ],
      stand: "Stand at the foot of rue de Rennes with the modern station behind you; the old one faced this square.",
      story: "At the Café de Versailles on this square, Matisse's students met; in 1908 the Swede Grünewald signed up his friends here. Up rue de Rennes lived the Americans who made Matisse: Leo Stein called Woman with a Hat the nastiest smear of paint he had ever seen, and bought it for 400 francs.",
      fact: "Not one Finn is recorded at Matisse's school. About forty Swedes were.",
      quiz: { q: "Five hundred francs asked. What did the buyer pay?", a: "Four hundred." }
    },
    {
      id: "vavin", n: 4, sticker: "dove", accent: "#F5C518", accentInk: "#141414",
      title: "Carrefour Vavin", place: "Balzac, Le Dôme, La Rotonde, La Coupole", time: "18:33", leg: "then 250 m east to stop 5",
      coord: [2.32905, 48.84215],
      audio: "audio/ep-04.mp3", audioLabel: "Rodin sends Matisse away · 6 min",
      panels: "comic/panels-04.jpg",
      captions: [
        "Paris, 1899. Henri Matisse, unknown, brings his drawings to Auguste Rodin.",
        "Rodin's verdict. “A facile hand. Draw fussier. Come back.”",
        "Matisse never went back. “Facile? That was false.”",
        "Instead he hired Rodin's own model, Bevilacqua, for up to 500 sittings.",
        "Rodin's own Balzac: shown in 1898, mocked, refused, kept at home.",
        "Unveiled on this island on 2 July 1939, forty-one years later."
      ],
      then: { src: "art/rol-le-dome-1931.jpg", credit: "Le Dôme, photographed by Agence Rol, 25 August 1931. BnF, public domain." },
      more: [
        { src: "art/balzac-rodin-vavin.jpg", credit: "Rodin's Balzac at carrefour Vavin today. Photo Celette, CC BY-SA 4.0." },
        { src: "art/matisse-portrait-de-bevilacqua.jpg", credit: "Henri Matisse, Portrait de Bevilacqua, c. 1900. Musée des Beaux-Arts de Bordeaux. Photo Tylwyth Eldar, CC BY-SA 4.0." },
        { src: "art/rol-la-rotonde-1924.jpg", credit: "La Rotonde, Agence Rol, 1924. BnF, public domain." }
      ],
      stand: "Stand on the wide pavement in front of Le Dôme, facing the statue on the island.",
      story: "In 1899 Rodin told the unknown Matisse he had a facile hand and to come back with fussier drawings. He never went back; he hired Rodin's model instead. Rodin's own Balzac was refused in 1898 and stood here only in 1939. At La Rotonde a broke painter could pay with a drawing.",
      fact: "Picasso's Dove of Peace (1949) was one of Matisse's pet pigeons, rehomed when his building banned the aviary. The island is named place Pablo-Picasso.",
      quiz: { q: "How did a painter with no money pay his bill at La Rotonde?", a: "With a drawing, which the owner kept until the painter could pay." }
    },
    {
      id: "door", n: 5, sticker: "swallow", accent: "#141414", accentInk: "#FAF6EE",
      title: "Matisse's front door", place: "132 boulevard du Montparnasse", time: "18:45", leg: "the last stop; back via rue de la Gaîté",
      coord: [2.331957, 48.841013],
      audio: "audio/ep-05.mp3", audioLabel: "A swallow over a stain · 4 min",
      panels: "comic/panels-05.jpg",
      frames: [
        { x: 0.030, y: 0.025, w: 0.455, h: 0.300 }, { x: 0.515, y: 0.025, w: 0.455, h: 0.300 },
        { x: 0.030, y: 0.350, w: 0.455, h: 0.300 }, { x: 0.515, y: 0.350, w: 0.455, h: 0.300 },
        { x: 0.030, y: 0.675, w: 0.455, h: 0.300 }, { x: 0.515, y: 0.675, w: 0.455, h: 0.300 }
      ],
      captions: [
        "1941. Matisse, aged 71, after a cancer operation, asks for three or four years.",
        "Summer 1946, in his flat at number 132. A stain on the wall.",
        "He cuts a swallow from writing paper and pins it over the stain.",
        "Then another shape, and another, until the wall is Océanie: sky and sea.",
        "Zika Ascher calls about scarves, sees the walls, prints them on linen: 30 copies.",
        "1961, New York. MoMA hangs his cut-out The Boat upside down for 47 days. Nobody notices."
      ],
      then: { src: "art/matisse-oceanie-le-ciel-1946.jpg", credit: "Henri Matisse, Océanie, le ciel, 1946, printed on linen 1948. Public domain in the EU." },
      more: [],
      stand: "Stand opposite the doorway of number 132. A plain residential building, no plaque.",
      story: "Matisse kept a flat here. In the summer of 1946 there was a stain on the wall; he pinned a paper swallow over it, then another shape, and another, until the wall was Tahiti. The cut-outs, the works he is most loved for, began as home repair.",
      fact: "In 1961 MoMA hung his cut-out The Boat upside down for 47 days. About 116,000 visitors walked past. The guard: \"You don't know what's up and you don't know what's down and neither do we.\"",
      quiz: { q: "What did he pin over the stain on this wall in 1946?", a: "A paper swallow. The cut-outs began." },
      finale: true
    },
    {
      id: "steins", n: 6, bonus: true, sticker: "frame", accent: "#1F3A93", accentInk: "#FAF6EE",
      title: "The Steins and the school", place: "27 rue de Fleurus · 58 rue Madame", time: "bonus",
      coord: [2.329331, 48.846924],
      audio: "audio/ep-06.mp3", audioLabel: "How the Steins made Matisse · 5 min",
      panels: "comic/panels-06.jpg",
      captions: [
        "1904. Michael and Sarah Stein hang Matisse's paintings four and five high at 58 rue Madame.",
        "1908. Sarah Stein and the Swede Carl Palme talk him into opening a school. “Teach them.”",
        "Over a hundred students, all but three foreigners, more than half Scandinavian.",
        "First critique: huge canvases of tortured shapes and garish colour.",
        "Matisse walks out, comes back with a plaster Greek head, sets it in the middle. “The antique first.”",
        "1911. “Monday to Saturday I tried to turn sheep into lions.” He closes the school."
      ],
      then: { src: "art/steins-studio-wall-1906.jpg", credit: "The studio at 27 rue de Fleurus, c. 1906. Woman with a Hat hangs top centre. Public domain." },
      more: [
        { src: "art/fougstedt-in-matisses-studio.jpg", credit: "Arvid Fougstedt, In Matisse's studio, c. 1910. Public domain." },
        { src: "art/academie-matisse-class-1909.jpg", credit: "Matisse and his students, 1909. Nasjonalmuseet, Oslo. Public domain." },
        { src: "art/matisse-portrait-of-sarah-stein-1916.jpg", credit: "Henri Matisse, Portrait of Sarah Stein, 1916. SFMOMA. Public domain." }
      ],
      story: "Leo and Gertrude Stein at 27 rue de Fleurus, Michael and Sarah at 58 rue Madame: the family who bought the wild beasts and talked Matisse into a school. A plaster Greek head at the first critique; sheep into lions; nineteen paintings lost to the war in Berlin.",
      fact: "Picasso needed eighty or ninety sittings for Gertrude's portrait. Told it did not look like her: \"She will.\"",
      quiz: { q: "What did Matisse put in the middle of the room at the first critique of his school?", a: "A plaster cast of an antique Greek head." }
    },
    {
      id: "garden", n: 7, bonus: true, sticker: "leaf", accent: "#2E7D4F", accentInk: "#FAF6EE",
      title: "The garden two friends painted", place: "Jardin du Luxembourg (gates close 18:15)", time: "bonus",
      coord: [2.33265, 48.84555],
      audio: "audio/ep-07.mp3", audioLabel: "The garden turned into Tahiti · episode coming",
      panels: "comic/panels-07.jpg",
      captions: [
        "About 1898. Matisse and Marquet, broke, carry easels into the Luxembourg garden.",
        "Same alley, same year, 1901. Two canvases.",
        "Marquet paints the trees quietly, in grey-green.",
        "Matisse paints a red tree, two pink trees, blue shadows. No palace, no statue. “That is not Paris.”",
        "1906. The Russian collector Shchukin buys it. It hangs today in Saint Petersburg.",
        "A scholar: without the signature, you would hardly take it for Paris. “Tahiti?”"
      ],
      then: { src: "art/matisse-luxembourg-gardens-1901.jpg", credit: "Henri Matisse, Le Jardin du Luxembourg, c. 1901. Hermitage. Public domain." },
      more: [
        { src: "art/marquet-alley-luxembourg-1901.jpg", credit: "Albert Marquet, An Alley in the Jardin du Luxembourg, 1901. Hermitage. Public domain." },
        { src: "art/namik-ismail-carpeaux-fountain-1924.jpg", credit: "Namık İsmail, Carpeaux Fountain in Paris, 1924. Istanbul. Public domain." },
        { src: "art/rousseau-monument-to-chopin-1909.jpg", credit: "Henri Rousseau, Monument to Chopin, 1909. Hermitage. Public domain." }
      ],
      story: "From about 1898 Matisse and Marquet painted this garden side by side. Matisse's alley has a red tree and blue shadows and no Paris in it at all; a scholar said that without the signature you would not know. It hangs in Saint Petersburg next to Marquet's.",
      fact: "In 1922 the State bought a Matisse for the museum at the garden's corner: seventeen years after the wild beasts, the first Matisse bought for a Paris museum.",
      quiz: { q: "Which city holds both friends' paintings of these alleys today?", a: "Saint Petersburg, in the Hermitage." }
    }
  ],
  /* the cafés and the vanished one: small cup markers with a card, no episode */
  pois: [
    { id: "dome", name: "Le Dôme", sub: "108 bd du Montparnasse · opened 1898", coord: [2.328911, 48.84202],
      text: "Headquarters of the German painters, the Dômiers: Rudolf Levy, Hans Purrmann, Walter Bondy, Albert Weisgerber. Purrmann and Levy later ran Matisse's school for him. A Swedish corner too. Matisse himself is not recorded here: these were his students' cafés.",
      img: "art/rol-le-dome-1931.jpg", credit: "Agence Rol, 25 August 1931. BnF, public domain." },
    { id: "rotonde", name: "La Rotonde", sub: "105 bd du Montparnasse · opened 1911", coord: [2.329132, 48.842361],
      text: "Victor Libion let painters with no money pay with a drawing, kept until they could pay. Kiki wrote in 1938: \"That blessed Rotonde, going there was like going home. Old Libion was the best of men.\" The story goes that women had to wear a hat to sit in the artists' room, so the teenage Kiki made herself one.",
      img: "art/rol-la-rotonde-1924.jpg", credit: "Agence Rol, 1924. BnF, public domain." },
    { id: "select", name: "Le Select", sub: "99 bd du Montparnasse · opened 1923", coord: [2.328367, 48.842614],
      text: "The late arrival of the four, open all night from the start, the Americans' café of the 1920s.",
      img: "art/select-2011.jpg", credit: "Le Select in 2011. Photo DIMSFIKAS (Greek Wikipedia), CC BY-SA 3.0." },
    { id: "coupole", name: "La Coupole", sub: "102 bd du Montparnasse · opened 20 December 1927", coord: [2.328069, 48.8423],
      text: "Built by two managers of the Dôme who had tried to buy it and failed. Opening night: more than 2,000 guests, about 1,200 bottles of champagne, the police at five in the morning. Twenty-seven painters decorated the pillars, Marie Vassilieff among them. Legend says they were paid in drinks; the invoice, found in 1993, says 23,000 francs.",
      img: "art/coupole-facade.jpg", credit: "La Coupole today. Photo Britchi Mirela, CC BY-SA 4.0." },
    { id: "closerie", name: "La Closerie des Lilas", sub: "171 bd du Montparnasse · the poets' café", coord: [2.335975, 48.840102],
      text: "The poet Paul Fort's Tuesdays, with Apollinaire and Jarry; Apollinaire brought Picasso here in 1905. On the terrace Fitzgerald handed Hemingway the manuscript of The Great Gatsby. Across the road stood the Bal Bullier, where the Delaunays danced the tango in painted clothes; Jules Flandrin, Matisse's classmate under Moreau, painted it in 1931.",
      img: "art/closerie-des-lilas-1909.jpg", credit: "La Closerie des Lilas, postcard, 1909. Public domain." },
    { id: "versailles", name: "Café de Versailles (gone)", sub: "3 place de Rennes, now place du 18-Juin-1940", coord: [2.324437, 48.844121],
      text: "Facing the old station. Matisse's students met here; in 1908 the Swede Isaac Grünewald signed up his friends for the school over discussions at these tables. The management seated \"these good lads\" (Matisse, Marie Laurencin, Vlaminck among them) at the back, away from the window." }
  ],
  dinner: [
    { q: "Upside down for 47 days at MoMA: how many visitors passed it before a stockbroker noticed?", a: "About 116,000." },
    { q: "What did Leo Stein pay for Woman with a Hat?", a: "400 francs. Matisse had asked 500." },
    { q: "Which Nordic country sent no student to Matisse's school?", a: "Finland." },
    { q: "Why could Vassilieff's canteen ignore the curfew?", a: "It was a private club, not a restaurant." },
    { q: "What did Matisse pin over the stain on his wall?", a: "A paper swallow." },
    { q: "In 1913 students in Chicago put Matisse on trial under what name?", a: "\"Henry Hair Mattress\", and burned copies of Blue Nude." }
  ]
};
