// The home page: what the study is about, at a glance. Same content as
// datasets/SidsDataset/README.md (the four parts and their tables), laid out
// to be read rather than navigated: the top bar already has the tabs.

const PARTS = [
  {
    n: 1,
    title: 'What explains results',
    answers: 'What we vary, and slice results by',
    hue: 0,
    groups: [
      {
        title: 'Knowledge structure',
        lead: 'How the edited knowledge is connected to the rest, and so what can follow from it.',
        tables: [
          {
            caption: 'Box',
            head: ['Box', 'Holds', 'Example'],
            rows: [
              ['ABox', 'A fact about one thing', 'Paris is the capital of France.'],
              ['TBox', 'A rule about a whole class', 'Every capital is a city.'],
              ['RBox', 'A property of a relation', '"Located in" is transitive.'],
            ],
          },
          {
            caption: 'Relation property',
            head: ['Property', 'Rule'],
            rows: [
              ['Inverse', 'a R b means b S a'],
              ['Symmetry', 'a R b means b R a'],
              ['Functional', 'one value per subject'],
              ['Subproperty', 'a R b implies a S b'],
              ['Transitivity', 'a R b and b R c give a R c'],
              ['Role chain', 'a R b and b S c give a T c'],
              ['Inheritance', 'a class rule passes to its members'],
              ['Cardinality', 'removing one value leaves the others'],
              ['Instantiation', 'an RBox property applied to two things'],
            ],
          },
          {
            caption: 'Derivability',
            head: ['Value', 'Meaning'],
            rows: [
              ['Stored', 'stated everywhere, so the model holds it directly'],
              ['Derived', 'hardly ever stated, but follows from facts the model holds'],
            ],
          },
        ],
      },
      {
        title: 'Operation',
        lead: 'Which kind of belief change an editor handles. Insert and delete are paired with a replace record.',
        tables: [
          {
            head: ['Operation', 'Does', 'Right answer after'],
            rows: [
              ['Insert (expansion)', 'adds a made-up fact', 'the new answer'],
              ['Replace (revision)', 'swaps a held fact for a false one', 'the new answer, never the old'],
              ['Delete (contraction)', 'removes a held fact', 'no longer the old answer'],
            ],
          },
        ],
      },
      {
        title: 'Determinacy',
        lead: 'Whether the edit forces one right answer. Indeterminate questions list their valid outcomes as worlds (Hase et al. 2024).',
        tables: [
          {
            head: ['Label', 'Meaning'],
            rows: [
              ['Determinate', 'every valid way of holding the knowledge gives one answer'],
              ['Background beliefs', 'depends on how the model stored a related fact'],
              ['Derived beliefs', 'depends on which premise of a derived edit gives way'],
            ],
          },
        ],
      },
      {
        title: 'Editing method',
        lead: 'Which approach to editing propagates and stays contained.',
        tables: [
          {
            head: ['Family', 'Methods'],
            rows: [
              ['Fine-tuning', 'FT-M, LoRA'],
              ['Locate then edit', 'ROME, AlphaEdit, FiDAL'],
              ['Neuron editing', 'FiNE'],
              ['Portability editors', 'IFMET, LTI, LoCo'],
            ],
          },
        ],
      },
    ],
  },
  {
    n: 2,
    title: 'How we measure',
    answers: 'How we observe what an edit did',
    hue: 70,
    groups: [
      {
        title: 'Question types',
        lead: 'From the edit outwards: everything that should change, then what must not.',
        wide: true,
        tables: [
          {
            head: ['Asks', 'Question type', 'Per record'],
            rows: [
              ['Did the edit take?', 'Direct, Paraphrase, Cross-lingual (zh, es)', '1, 1, 2'],
              ['Does it survive logic?', 'Propositional: negation, conjunction, disjunction', '3'],
              ['Does it spread?', 'Related (a stored answer that must change), Derived (an answer never stated, 2 hops)', '1, 3 to 4'],
              ['Does it stay contained?', 'Unrelated near, Unrelated far', '1, 1'],
            ],
          },
        ],
      },
      {
        title: 'Task types',
        lead: 'What a related or derived question makes the model do with the edit.',
        tables: [
          {
            head: ['Task', 'Asks the model to'],
            rows: [
              ['Answer', 'give the conclusion itself'],
              ['Composition', 'follow the edit, then look up an unconnected fact'],
              ['Binding', 'reach the subject by another name it knows'],
              ['Application', 'use the conclusion in a practical task'],
            ],
          },
        ],
      },
      {
        title: 'Metrics',
        lead: 'Our names say what is measured; the usual term is beside each.',
        tables: [
          {
            head: ['Metric', 'Usual name', 'Over'],
            rows: [
              ['Rewrite', 'reliability', 'direct'],
              ['Generalizability', 'portability', 'paraphrase, related, derived'],
              ['Cross-lingual', 'cross-lingual portability', 'cross-lingual'],
              ['Logical consistency', 'ours', 'propositional'],
              ['Specificity', 'locality', 'unrelated near, far'],
              ['Answer diversity', 'fluency', 'English answers'],
              ['Grammar', 'ours', 'English answers'],
              ['Contraction abstention', 'ours', 'delete records'],
            ],
          },
        ],
      },
      {
        title: 'Inside generalizability',
        lead: 'Reported part by part, and per relation property, task, hop count and logic.',
        tables: [
          {
            head: ['Part', 'Passes when'],
            rows: [
              ['Paraphrase', 'the reworded question gets the new answer'],
              ['Related', 'the stored answer changes'],
              ['Derived (headline)', 'determinate questions the unedited model knew get the new answer'],
            ],
          },
          {
            caption: 'Main experiment probes',
            head: ['Probe', 'Shows'],
            rows: [
              ['Indeterminate change', 'stayed original, moved to a world, or to no world'],
              ['Hinted', 'the model holds the edit but does not connect it'],
              ['Reasoning', 'the first step that goes wrong'],
            ],
          },
        ],
      },
    ],
  },
  {
    n: 3,
    title: 'Controls',
    answers: 'What we hold steady, or vary only to show a result generalizes',
    hue: 150,
    groups: [
      {
        title: 'Topic',
        lead: 'A finding about rules is not secretly a finding about one domain. Every topic has the same shape.',
        pills: ['Geography', 'People', 'History', 'Finance', 'Biology', 'Physics', 'Literature and arts', 'Technology', 'Mathematics', 'Grammar'],
      },
      {
        title: 'Models',
        lead: 'A finding holds across model families and sizes.',
        pills: ['Qwen3-4B-Instruct', 'Olmo-3-7B-Instruct', 'Llama-3.1-8B-Instruct', 'Mistral-7B-Instruct'],
      },
      {
        title: 'Split',
        lead: 'Tuning never sees the test set: the splits share no fact or subject.',
        tables: [
          {
            head: ['Split', 'Records', 'Used for'],
            rows: [
              ['Dev', '120', 'hyperparameter tuning'],
              ['Main', '600', 'the results we report'],
            ],
          },
        ],
      },
    ],
  },
  {
    n: 4,
    title: 'Validity checks',
    answers: 'Why the records can be trusted',
    hue: 220,
    groups: [
      {
        title: 'Logic verification',
        lead: 'Guards against wrong logic or an unsound translation from English to logic. Every record is checked with the HermiT reasoner.',
        tables: [
          {
            head: ['Check', 'Passes when'],
            rows: [
              ['Premises', 'a derived edit’s premises entail the original fact'],
              ['Before the edit', 'every original answer follows'],
              ['Determinate', 'the answer follows in every world'],
              ['Indeterminate', 'each world gives its own answer'],
              ['Worlds', 'each is consistent, every minimal repair is one'],
              ['Justifications', 'the proof matches the stated property and hops'],
            ],
          },
        ],
      },
      {
        title: 'Model audit',
        lead: 'Guards against testing knowledge the models never had. Each model answers before any edit.',
        tables: [
          {
            head: ['Check', 'Passes when'],
            rows: [
              ['Original fact held', 'direct and paraphrase get the original (tagged per model)'],
              ['Premises and bridges held', 'the model knows what a question relies on'],
              ['Insert is new', 'no model already holds an inserted fact'],
            ],
          },
        ],
      },
      {
        title: 'Review',
        lead: 'Humans and agents (Codex and Claude) mark every record and question green or red under two rules.',
        tables: [
          {
            head: ['Rule', 'Asks'],
            rows: [
              ['Clear and sensible', 'is the edit, each question and each world unambiguous?'],
              ['Serves the purpose', 'does the record help answer the question we study?'],
            ],
          },
          {
            caption: 'What review catches (share of flags)',
            head: ['Problem', 'Share', 'Looks like'],
            rows: [
              ['Answerable without the knowledge', '73%', 'a yes/no default passes, the prompt gives it away, the property is part of the word’s meaning'],
              ['Logic and link errors', '10%', 'does not follow from the edit, answer does not move, wrong gold'],
              ['Ambiguous framing', '8%', 'more than one fair answer, unclear negation or scope'],
              ['Record hygiene', '5%', 'out-of-date notes, wrong labels, evidence problems'],
              ['Edit design', '4%', 'clashes with firmly held knowledge, contested facts'],
            ],
          },
        ],
      },
      {
        title: 'Automated rules',
        lead: 'Guards against leaks, duplicates, missing evidence and gaps in coverage. Rules 3 to 15, some with an LLM judge.',
        tables: [
          {
            head: ['Group', 'Checks'],
            rows: [
              ['Wording', 'stable subjects, no answer in the prompt'],
              ['Uniqueness', 'no repeated edits, no shared facts between splits'],
              ['Evidence', 'every fact backed, related and derived answers change'],
              ['Measurement', 'specificity catches leaks, yes/no balanced'],
              ['Coverage', 'every record has its queries, properties and tasks balanced'],
              ['Runs', 'every method runs on every edit, operations paired'],
            ],
          },
        ],
      },
    ],
  },
  {
    n: 5,
    title: 'Hyperparameter tuning',
    answers: 'How each method is set up fairly before it is compared',
    hue: 290,
    groups: [
      {
        title: 'Search',
        lead: 'Tuned per model on the 120 dev records. One rule for every method: the best mean of paraphrase, generalizability, cross-lingual and logical consistency, among settings that pass the rewrite, fluency and specificity gates.',
        wide: true,
        tables: [
          {
            head: ['Stage', 'Design', 'Finds'],
            rows: [
              ['1. Screen', 'two-level factorial: every setting at a low and a high value, all crossed, plus centre runs', 'which settings matter, and in which direction'],
              ['2. Sweep', 'one at a time: 8 to 10 values of each setting that matters, the others held', 'the exact value of each setting'],
            ],
          },
        ],
      },
      {
        title: 'Hyperparameters per method',
        lead: 'Which matter is preliminary, from the first search.',
        wide: true,
        tables: [
          {
            head: ['Method', 'Matter', 'Matter little'],
            rows: [
              ['FT-M', 'layer, norm constraint', 'learning rate, steps, weight decay'],
              ['LoRA', 'learning rate, alpha, target matrices, layer window', 'rank, steps, weight decay'],
              ['LoCo', 'learning rate, steps, alpha, constraint', 'rank, implication count and length, completion weight'],
              ['FiNE', 'learning rate, neuron count', 'alpha, beta, gamma, last layer'],
              ['ROME', 'clamp, layer, v_lr, gradient steps', 'KL weight, weight decay'],
              ['AlphaEdit', 'clamp, v_lr, layer window', 'mom2 weight, KL weight, weight decay'],
              ['FiDAL', 'candidate layers, clamp, v_lr', 'gradient steps, mom2 weight, KL weight'],
              ['IFMET', 'NLL weight, v_lr', 'support count, deep layers, mom2 weight, KL weight'],
              ['LTI', 'clamp, layer window', 'v_lr, NLL weight, mid layers, mid and last KL, mom2 weight'],
            ],
          },
        ],
      },
      {
        title: 'Findings so far',
        lead: 'From the first search on 40 dev edits, not yet from the re-tuning on the 120 dev records.',
        wide: true,
        tables: [
          {
            head: ['Finding', 'Detail'],
            rows: [
              ['Strength matters most', 'about 6 points on the objective; layers 4.5, training signal 4, regularisers 1.6 (noise)'],
              ['Model over method', '45% of the variation is the model, 28% the method; Llama is easiest to edit well, Olmo hardest'],
              ['Two regimes', 'training methods are set by the specificity gate; locate-then-edit methods by rewrite, then flat'],
              ['One trade-off', 'paraphrase, generalizability and cross-lingual rise together and against specificity; nothing buys logical consistency'],
              ['Rankings depend on the gate', 'at specificity 0.7 the training methods lead; at 0.8 all nine sit within 7 points'],
              ['Partly overfitted picks', 'resampled records repeat the same pick 45% of the time; the conclusions hold regardless'],
            ],
          },
        ],
      },
    ],
  },
]

function StudyTable({ caption, head, rows }) {
  return (
    <div className="study-table-wrap">
      {caption && <div className="study-caption">{caption}</div>}
      <table className="study-table">
        <thead>
          <tr>{head.map((h) => <th key={h}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r[0]}>{r.map((c, i) => <td key={i}>{c}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Home() {
  return (
    <div className="home">
      <section className="home-hero">
        <h1>Sid's Dataset</h1>
        <p className="home-byline">A knowledge-editing benchmark, by Sid</p>
        <p className="home-intro">
          Published benchmarks mostly edit simple facts and test generalization with paraphrases. Sid's Dataset
          edits three kinds of knowledge (facts, class rules and properties of relations) through three belief
          revision operations. It then asks questions that need different kinds of reasoning: whether the edit
          took, whether it survives logic, whether it spreads to what follows from it, and whether it stays
          contained. The right answer to every question is worked out in advance, including when it depends on
          how the model stored its knowledge.
        </p>
        <blockquote className="home-question">
          Under what kinds of knowledge and belief revision operations does a knowledge edit succeed, propagate
          to what follows from it, and stay contained?
        </blockquote>
      </section>

      <ol className="study-overview">
        {PARTS.map((p) => (
          <li key={p.n} className="study-overview-item" style={{ '--part-shift': p.hue }}>
            <span className="study-num">{p.n}</span>
            <span className="study-overview-title">{p.title}</span>
            <span className="study-overview-answers">{p.answers}</span>
            <span className="study-overview-contains">{p.groups.map((g) => g.title).join(' · ')}</span>
          </li>
        ))}
      </ol>

      {PARTS.map((p) => (
        <section key={p.n} className="study-part" style={{ '--part-shift': p.hue }}>
          <header className="study-part-head">
            <span className="study-num">{p.n}</span>
            <div>
              <h2>{p.title}</h2>
              <p>{p.answers}</p>
            </div>
          </header>
          <div className="study-groups">
            {p.groups.map((g) => (
              <article key={g.title} className={`study-group${g.wide ? ' is-wide' : ''}`}>
                <h3>{g.title}</h3>
                <p className="study-lead">{g.lead}</p>
                {g.pills && (
                  <div className="study-pills">
                    {g.pills.map((x) => <span key={x} className="study-pill">{x}</span>)}
                  </div>
                )}
                {g.tables?.map((t, i) => <StudyTable key={i} {...t} />)}
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
