import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactHlsPlayer from 'react-hls-player';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MetaverseWorld = ({ walletAddress, isConnected }) => {
  const [worldData, setWorldData] = useState(null);
  const [activeArea, setActiveArea] = useState('live_stream');
  const [airdrops, setAirdrops] = useState([]);
  const [nfts, setNfts] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [userGallery, setUserGallery] = useState(null);
  const [currentStream, setCurrentStream] = useState(null);
  const [streamUrl, setStreamUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Load world data
  useEffect(() => {
    loadWorldData();
    loadAirdrops();
    loadNFTs();
    loadProposals();
    if (isConnected) {
      loadUserGallery();
    }
  }, [isConnected]);

  const loadWorldData = async () => {
    try {
      const response = await axios.get(`${API}/metaverse/world`);
      setWorldData(response.data);
    } catch (error) {
      console.error('Error loading world data:', error);
    }
  };

  const loadAirdrops = async () => {
    try {
      const response = await axios.get(`${API}/metaverse/airdrop/available`);
      setAirdrops(response.data);
    } catch (error) {
      console.error('Error loading airdrops:', error);
    }
  };

  const loadNFTs = async () => {
    try {
      const response = await axios.get(`${API}/metaverse/marketplace/nfts`);
      setNfts(response.data);
    } catch (error) {
      console.error('Error loading NFTs:', error);
    }
  };

  const loadProposals = async () => {
    try {
      const response = await axios.get(`${API}/metaverse/voting/proposals`);
      setProposals(response.data);
    } catch (error) {
      console.error('Error loading proposals:', error);
    }
  };

  const loadUserGallery = async () => {
    try {
      const response = await axios.get(`${API}/metaverse/gallery/${walletAddress}`);
      setUserGallery(response.data);
    } catch (error) {
      console.error('Error loading user gallery:', error);
    }
  };

  const claimAirdrop = async (airdropId) => {
    if (!isConnected) {
      setMessage('Bitte verbinde deine Wallet!');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API}/metaverse/airdrop/claim`, {
        wallet_address: walletAddress,
        airdrop_id: airdropId
      });
      
      setMessage(response.data.message);
      await loadAirdrops();
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Fehler beim Claimen des Airdrops');
    } finally {
      setLoading(false);
    }
  };

  const buyNFT = async (nftId) => {
    if (!isConnected) {
      setMessage('Bitte verbinde deine Wallet!');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API}/metaverse/marketplace/buy`, {
        wallet_address: walletAddress,
        nft_id: nftId
      });
      
      setMessage(response.data.message);
      await loadNFTs();
      await loadUserGallery();
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Fehler beim NFT-Kauf');
    } finally {
      setLoading(false);
    }
  };

  const castVote = async (proposalId, voteOption) => {
    if (!isConnected) {
      setMessage('Bitte verbinde deine Wallet!');
      return;
    }

    try {
      setLoading(true);
      await axios.post(`${API}/metaverse/voting/vote`, {
        wallet_address: walletAddress,
        proposal_id: proposalId,
        vote_option: voteOption
      });
      
      setMessage('Vote erfolgreich abgegeben!');
      await loadProposals();
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Fehler beim Voten');
    } finally {
      setLoading(false);
    }
  };

  if (!worldData) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900 text-white">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-lg border-b border-purple-500/20 p-4">
        <div className="container mx-auto flex items-center justify-between">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
            {worldData.world_name}
          </h1>
          <div className="text-sm text-gray-400">
            {isConnected ? `Verbunden: ${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}` : 'Nicht verbunden'}
          </div>
        </div>
      </div>

      {/* Message Display */}
      {message && (
        <div className="bg-purple-500/20 border border-purple-500/50 rounded-lg p-4 m-4 text-center">
          {message}
          <button onClick={() => setMessage('')} className="ml-4 text-purple-400 hover:text-purple-300">
            ✕
          </button>
        </div>
      )}

      {/* Navigation */}
      <div className="p-4">
        <div className="flex flex-wrap justify-center gap-4 mb-8">
          {worldData.areas.map(area => (
            <button
              key={area.id}
              onClick={() => setActiveArea(area.id)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                activeArea === area.id
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg transform scale-105'
                  : 'bg-black/30 border border-purple-500/30 text-purple-300 hover:bg-black/50'
              }`}
            >
              {area.name}
            </button>
          ))}
        </div>

        {/* Area Content */}
        <div className="container mx-auto">
          {/* Live Stream Arena */}
          {activeArea === 'live_stream' && (
            <div className="text-center">
              <h2 className="text-4xl font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-pink-400">
                🎥 Live Stream Arena
              </h2>
              
              <div className="bg-black/40 backdrop-blur-lg rounded-2xl p-8 border border-red-500/20 max-w-4xl mx-auto">
                <div className="relative">
                  <div className="bg-gradient-to-br from-red-500/20 to-pink-500/20 rounded-xl p-8 mb-6">
                    <div className="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold animate-pulse">
                      LIVE
                    </div>
                    
                    {/* Avatar/Character Display */}
                    <div className="flex items-center justify-center mb-6">
                      <div className="w-64 h-64 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center relative overflow-hidden">
                        <div className="text-8xl">🎮</div>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent"></div>
                      </div>
                    </div>
                    
                    <h3 className="text-2xl font-bold mb-2">KryptoMurat Live</h3>
                    <p className="text-gray-300 mb-4">Willkommen in der Metaverse-Welt!</p>
                    
                    <div className="flex items-center justify-center space-x-4 text-sm text-gray-400">
                      <span>👥 1,234 Zuschauer</span>
                      <span>⏰ Live seit 2:34:56</span>
                    </div>
                  </div>
                  
                  <button className="bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white font-bold py-3 px-8 rounded-lg transition-all duration-200 transform hover:scale-105">
                    Stream Beitreten
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* NFT Gallery */}
          {activeArea === 'nft_gallery' && (
            <div>
              <h2 className="text-4xl font-bold mb-8 text-center text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-400">
                🎭 NFT Gallery
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {nfts.map(nft => (
                  <div key={nft.id} className="bg-black/40 backdrop-blur-lg rounded-xl p-6 border border-yellow-500/20 hover:border-yellow-500/50 transition-all duration-200">
                    <div className="aspect-square bg-gradient-to-br from-yellow-400/20 to-orange-400/20 rounded-lg mb-4 flex items-center justify-center">
                      <img src={nft.image_url} alt={nft.name} className="w-full h-full object-cover rounded-lg" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">{nft.name}</h3>
                    <p className="text-gray-400 mb-4">{nft.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-2xl font-bold text-yellow-400">{nft.price} MURAT</span>
                      <button
                        onClick={() => buyNFT(nft.id)}
                        disabled={loading}
                        className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-bold py-2 px-4 rounded-lg transition-all duration-200 disabled:opacity-50"
                      >
                        {loading ? 'Kaufe...' : 'Kaufen'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* User Gallery */}
              {userGallery && (
                <div className="bg-black/40 backdrop-blur-lg rounded-xl p-6 border border-yellow-500/20">
                  <h3 className="text-2xl font-bold mb-4">Deine NFT-Sammlung</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {userGallery.owned_nfts.map(nft => (
                      <div key={nft.id} className="bg-black/60 rounded-lg p-4 border border-yellow-500/30">
                        <div className="aspect-square bg-gradient-to-br from-yellow-400/20 to-orange-400/20 rounded-lg mb-2 flex items-center justify-center">
                          <img src={nft.image_url} alt={nft.name} className="w-full h-full object-cover rounded-lg" />
                        </div>
                        <h4 className="font-bold">{nft.name}</h4>
                        <p className="text-sm text-gray-400">{nft.rarity}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 text-center">
                    <p className="text-gray-400">Gesamt: {userGallery.total_owned} NFTs • Ausgegeben: {userGallery.total_spent} MURAT</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Voting Chamber */}
          {activeArea === 'voting_chamber' && (
            <div>
              <h2 className="text-4xl font-bold mb-8 text-center text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">
                🗳️ Voting Chamber
              </h2>
              
              <div className="space-y-6">
                {proposals.map(proposal => (
                  <div key={proposal.id} className="bg-black/40 backdrop-blur-lg rounded-xl p-6 border border-green-500/20">
                    <h3 className="text-2xl font-bold mb-4">{proposal.title}</h3>
                    <p className="text-gray-300 mb-6">{proposal.description}</p>
                    
                    <div className="space-y-3">
                      <h4 className="text-lg font-semibold text-green-400">Abstimmungsoptionen:</h4>
                      {proposal.options.map((option, index) => (
                        <button
                          key={index}
                          onClick={() => castVote(proposal.id, option)}
                          disabled={loading}
                          className="w-full bg-gradient-to-r from-green-500/20 to-blue-500/20 hover:from-green-500/30 hover:to-blue-500/30 border border-green-500/30 rounded-lg p-4 text-left transition-all duration-200 disabled:opacity-50"
                        >
                          <span className="font-semibold">{option}</span>
                        </button>
                      ))}
                    </div>
                    
                    <div className="mt-4 text-sm text-gray-400">
                      Endet am: {new Date(proposal.ends_at).toLocaleDateString('de-DE')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Airdrop Zone */}
          {activeArea === 'airdrop_zone' && (
            <div>
              <h2 className="text-4xl font-bold mb-8 text-center text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                🎁 Airdrop Zone
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {airdrops.map(airdrop => (
                  <div key={airdrop.id} className="bg-black/40 backdrop-blur-lg rounded-xl p-6 border border-purple-500/20 hover:border-purple-500/50 transition-all duration-200">
                    <div className="aspect-square bg-gradient-to-br from-purple-400/20 to-pink-400/20 rounded-lg mb-4 flex items-center justify-center">
                      <img src={airdrop.image_url} alt={airdrop.name} className="w-full h-full object-cover rounded-lg" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">{airdrop.name}</h3>
                    <p className="text-gray-400 mb-4">{airdrop.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-2xl font-bold text-purple-400">{airdrop.amount} MURAT</span>
                      <button
                        onClick={() => claimAirdrop(airdrop.id)}
                        disabled={loading}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-2 px-4 rounded-lg transition-all duration-200 disabled:opacity-50"
                      >
                        {loading ? 'Claimt...' : 'Claimen'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* VIP Lounge */}
          {activeArea === 'vip_lounge' && (
            <div className="text-center">
              <h2 className="text-4xl font-bold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-yellow-400">
                👑 VIP Lounge
              </h2>
              
              <div className="bg-black/40 backdrop-blur-lg rounded-2xl p-8 border border-yellow-500/20 max-w-4xl mx-auto">
                <div className="text-8xl mb-6">🍾</div>
                <h3 className="text-3xl font-bold mb-4">Exklusiver VIP-Bereich</h3>
                <p className="text-gray-300 mb-6">
                  Dieser Bereich ist für VIP-Mitglieder reserviert. Kaufe NFTs oder stake mehr MURAT Token für Zugang.
                </p>
                
                <div className="space-y-4 mb-8">
                  <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-lg p-4">
                    <h4 className="font-bold text-yellow-400">VIP-Vorteile:</h4>
                    <ul className="text-left text-gray-300 mt-2 space-y-1">
                      <li>• Exklusive NFT-Drops</li>
                      <li>• Private Streaming-Events</li>
                      <li>• Erhöhte Airdrop-Belohnungen</li>
                      <li>• Direkter Zugang zu KryptoMurat</li>
                    </ul>
                  </div>
                </div>
                
                <button className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-bold py-3 px-8 rounded-lg transition-all duration-200 transform hover:scale-105">
                  VIP-Zugang Freischalten
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MetaverseWorld;