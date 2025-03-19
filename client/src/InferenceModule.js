import React, { useState } from 'react';

const InferenceModule = () => {
  const [symptoms, setSymptoms] = useState('');
  const [result, setResult] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Normalize user input
    const normalizedSymptoms = symptoms
      .toLowerCase()
      .trim()
      .split(/[\s,]+/)
      .filter(symptom => symptom);

    try {
      const response = await fetch('/api/infer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms })
      });      
      const data = await response.text();
      setResult(data);
    } catch (error) {
      setResult('Error: ' + error.message);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Marine Envenomation Expert System</h1>
      <h2>Symptom Inference</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="Enter symptoms here..."
          rows="4"
          style={{ width: '100%', padding: '10px', fontSize: '1rem' }}
        />
        <br />
        <button type="submit" style={{ marginTop: '10px', padding: '10px 20px', fontSize: '1rem' }}>
          Submit
        </button>
      </form>
      {result && (
        <div
          style={{
            marginTop: '20px',
            padding: '10px',
            backgroundColor: '#f9f9f9',
            border: '1px solid #ddd',
            whiteSpace: 'pre-wrap'
          }}
        >
          {result}
        </div>
      )}
    </div>
  );
};

export default InferenceModule;
