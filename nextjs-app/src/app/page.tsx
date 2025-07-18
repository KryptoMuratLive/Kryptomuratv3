'use client';

import { useState, useEffect } from 'react';
import { useWeb3Modal } from '@web3modal/ethers/react';
import { useWeb3ModalProvider, useWeb3ModalAccount } from '@web3modal/ethers/react';
import { BrowserProvider } from 'ethers';
import axios from 'axios';
import { formatAddress, formatBalance, getAPYForDuration } from '@/lib/utils';
import { WalletData, StakingPosition, NFTAccess as NFTAccessType } from '@/types';
import Dashboard from '@/components/Dashboard';
import StoryGame from '@/components/StoryGame';
import StakingPanel from '@/components/StakingPanel';
import StreamingPanel from '@/components/StreamingPanel';
import AICreator from '@/components/AICreator';
import NFTAccessPanel from '@/components/NFTAccess';
import MobileNavigation from '@/components/MobileNavigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:3000';

export default function Home() {
  const { open } = useWeb3Modal();
  const { address, isConnected } = useWeb3ModalAccount();
  const { walletProvider } = useWeb3ModalProvider();
  
  // State management
  const [loading, setLoading] = useState(false);
  const [tokenBalance, setTokenBalance] = useState('0');
  const [stakingPositions, setStakingPositions] = useState<StakingPosition[]>([]);
  const [nftAccess, setNftAccess] = useState<NFTAccessType | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isMobile, setIsMobile] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  // Mobile detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Load user data when wallet connects
  useEffect(() => {
    if (isConnected && address) {
      connectWallet();
      loadUserData();
    }
  }, [isConnected, address]);

  const connectWallet = async () => {
    if (!address) return;
    
    try {
      setLoading(true);
      
      // Store connection in backend
      await axios.post(`${API_BASE}/api/wallet/connect`, {
        wallet_address: address,
        chain_id: 137
      });
      
    } catch (error) {
      console.error('Error connecting wallet:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserData = async () => {
    if (!address) return;
    
    try {
      // Load token balance
      const balanceResponse = await axios.get(`${API_BASE}/api/wallet/balance/${address}`);
      if (balanceResponse.data.success) {
        setTokenBalance(balanceResponse.data.data.balance);
      }
      
      // Load staking positions
      const stakingResponse = await axios.get(`${API_BASE}/api/staking/positions/${address}`);
      if (stakingResponse.data.success) {
        setStakingPositions(stakingResponse.data.data);
      }
      
      // Load NFT access
      const nftResponse = await axios.get(`${API_BASE}/api/nft/access/${address}`);
      if (nftResponse.data.success) {
        setNftAccess(nftResponse.data.data);
      }
      
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const createStakingPosition = async (amount: string, durationDays: number) => {
    if (!address || !amount) return;
    
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/api/staking/create`, {
        wallet_address: address,
        amount: amount,
        duration_days: durationDays
      });
      
      if (response.data.success) {
        await loadUserData();
        return { success: true, message: 'Staking-Position erfolgreich erstellt!' };
      }
      
      return { success: false, message: 'Fehler beim Erstellen der Staking-Position' };
    } catch (error) {
      console.error('Error creating staking position:', error);
      return { success: false, message: 'Fehler beim Erstellen der Staking-Position' };
    } finally {
      setLoading(false);
    }
  };

  const generateAIContent = async (prompt: string, contentType: string) => {
    if (!address || !prompt) return;
    
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/api/ai/generate`, {
        prompt,
        content_type: contentType,
        wallet_address: address
      });
      
      if (response.data.success) {
        return { success: true, content: response.data.data.content };
      }
      
      return { success: false, message: 'Fehler beim Generieren des AI-Contents' };
    } catch (error) {
      console.error('Error generating AI content:', error);
      return { success: false, message: 'Fehler beim Generieren des AI-Contents' };
    } finally {
      setLoading(false);
    }
  };

  // Touch handlers for swipe navigation
  const [swipeStartX, setSwipeStartX] = useState(0);
  
  const handleTouchStart = (e: React.TouchEvent) => {
    setSwipeStartX(e.touches[0].clientX);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const swipeEndX = e.changedTouches[0].clientX;
    const swipeDistance = swipeStartX - swipeEndX;
    
    if (Math.abs(swipeDistance) > 50) {
      const tabs = ['dashboard', 'story', 'staking', 'streaming', 'ai', 'nft'];
      const currentIndex = tabs.indexOf(activeTab);
      
      if (swipeDistance > 0 && currentIndex < tabs.length - 1) {
        setActiveTab(tabs[currentIndex + 1]);
      } else if (swipeDistance < 0 && currentIndex > 0) {
        setActiveTab(tabs[currentIndex - 1]);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900"
         onTouchStart={handleTouchStart}
         onTouchEnd={handleTouchEnd}>
      
      <Header 
        isConnected={isConnected}
        address={address}
        tokenBalance={tokenBalance}
        onConnectWallet={() => open()}
        loading={loading}
        isMobile={isMobile}
        showMobileMenu={showMobileMenu}
        setShowMobileMenu={setShowMobileMenu}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="container mx-auto px-4 py-4 md:py-8">
        {!isConnected ? (
          /* Mobile-Optimized Landing Page with Animated Background */
          <div className="relative text-center py-10 md:py-20 overflow-hidden">
            {/* Animated Background with Multiple Image Options */}
            <div className="absolute inset-0 z-0">
              {/* Multiple image format attempts */}
              <img 
                src="/web3-background.jpg" 
                alt="Jagd auf den Bitcoin"
                className="w-full h-full object-cover opacity-25"
                style={{
                  animation: 'float 8s ease-in-out infinite',
                  filter: 'blur(0.5px) brightness(0.8) contrast(1.2)'
                }}
                onError={(e) => {
                  console.log('JPG failed, trying PNG...');
                  const target = e.target as HTMLImageElement;
                  target.src = '/web3-background.png';
                  target.onerror = (e2) => {
                    console.log('PNG failed, trying different name...');
                    const target2 = e2.target as HTMLImageElement;
                    target2.src = '/jagd-auf-den-bitcoin.jpg';
                    target2.onerror = (e3) => {
                      console.log('All image attempts failed, hiding element');
                      const target3 = e3.target as HTMLImageElement;
                      target3.style.display = 'none';
                    };
                  };
                }}
              />
              
              {/* Enhanced Fallback Background with Bitcoin Hunt Theme */}
              <div 
                className="w-full h-full opacity-40"
                style={{
                  background: `
                    linear-gradient(135deg, 
                      rgba(251, 191, 36, 0.4) 0%, 
                      rgba(59, 130, 246, 0.4) 25%, 
                      rgba(139, 92, 246, 0.4) 50%, 
                      rgba(251, 191, 36, 0.4) 75%, 
                      rgba(16, 185, 129, 0.4) 100%
                    ),
                    radial-gradient(circle at 25% 25%, rgba(251, 191, 36, 0.5) 0%, transparent 50%),
                    radial-gradient(circle at 75% 75%, rgba(59, 130, 246, 0.5) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.5) 0%, transparent 50%)
                  `,
                  animation: 'float 12s ease-in-out infinite',
                  backgroundSize: '400% 400%'
                }}
              />
              
              {/* Enhanced Cyber Elements with Bitcoin Hunt Theme */}
              <div className="absolute inset-0 overflow-hidden">
                {/* Larger animated elements */}
                <div className="absolute top-16 left-16 w-24 h-24 bg-gradient-to-br from-yellow-500/40 to-orange-500/40 rounded-full animate-pulse"></div>
                <div className="absolute top-1/3 right-16 w-20 h-20 bg-gradient-to-br from-blue-500/40 to-purple-500/40 rounded-full animate-bounce"></div>
                <div className="absolute bottom-1/3 left-24 w-28 h-28 bg-gradient-to-br from-purple-500/40 to-pink-500/40 rounded-full animate-pulse"></div>
                <div className="absolute bottom-16 right-24 w-16 h-16 bg-gradient-to-br from-green-500/40 to-teal-500/40 rounded-full animate-bounce"></div>
                
                {/* Bitcoin Hunt Themed Symbols */}
                <div className="absolute top-24 left-40 text-5xl text-yellow-500/50 animate-spin-slow">₿</div>
                <div className="absolute top-48 right-40 text-4xl text-blue-500/50 animate-bounce">🎯</div>
                <div className="absolute bottom-48 left-48 text-6xl text-purple-500/50 animate-pulse">💎</div>
                <div className="absolute bottom-24 right-48 text-5xl text-green-500/50 animate-wiggle">🏆</div>
                
                {/* Additional Hunt Elements */}
                <div className="absolute top-64 left-64 text-3xl text-orange-500/40 animate-bounce">🎮</div>
                <div className="absolute top-80 right-64 text-4xl text-red-500/40 animate-pulse">🔍</div>
                <div className="absolute bottom-64 left-80 text-3xl text-cyan-500/40 animate-wiggle">⚡</div>
                <div className="absolute bottom-80 right-80 text-4xl text-pink-500/40 animate-spin-slow">🌟</div>
                
                {/* Animated Grid Lines - More Prominent */}
                <div className="absolute top-0 left-1/4 w-px h-full bg-gradient-to-b from-transparent via-yellow-500/30 to-transparent animate-pulse"></div>
                <div className="absolute top-0 right-1/4 w-px h-full bg-gradient-to-b from-transparent via-blue-500/30 to-transparent animate-pulse"></div>
                <div className="absolute top-1/4 left-0 w-full h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent animate-pulse"></div>
                <div className="absolute bottom-1/4 left-0 w-full h-px bg-gradient-to-r from-transparent via-orange-500/30 to-transparent animate-pulse"></div>
                
                {/* Central Focus Point */}
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-gradient-to-br from-yellow-500/20 to-orange-500/20 rounded-full animate-pulse"></div>
              </div>
              
              <div className="absolute inset-0 bg-gradient-to-br from-purple-900/60 via-blue-900/60 to-purple-900/60"></div>
            </div>

            <div className="relative z-10 max-w-4xl mx-auto">
              <h2 className="text-4xl md:text-6xl font-bold text-white mb-4 md:mb-6 leading-tight">
                <span className="inline-block animate-bounce">🚀</span>
                <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 animate-pulse">
                  STEIG EIN BEI WEB3!
                </span>
                <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                  KryptoMurat
                </span>
              </h2>
              
              <p className="text-xl md:text-2xl text-white mb-6 md:mb-8 max-w-3xl mx-auto px-4 font-semibold">
                🌐 Die ultimative Web3-Metaverse-Plattform! 
                <br/>
                <span className="text-yellow-300">Spiele, stake, streame und sammle in der digitalen Zukunft!</span>
              </p>
              
              {/* Animated Feature Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 mb-8 md:mb-12 px-4">
                <div className="bg-black/40 backdrop-blur-lg rounded-xl p-4 md:p-6 border border-orange-500/30 hover:border-orange-500/60 transition-all duration-300 transform hover:scale-105 hover:rotate-1">
                  <div className="text-3xl md:text-4xl mb-2 md:mb-4 animate-spin-slow">🪙</div>
                  <h3 className="text-lg md:text-xl font-bold text-orange-400 mb-2">MURAT Token</h3>
                  <p className="text-sm md:text-base text-gray-300">Stake für bis zu 8% APY, kaufe NFTs und schalte VIP-Bereiche frei!</p>
                </div>
                
                <div className="bg-black/40 backdrop-blur-lg rounded-xl p-4 md:p-6 border border-red-500/30 hover:border-red-500/60 transition-all duration-300 transform hover:scale-105 hover:-rotate-1">
                  <div className="text-3xl md:text-4xl mb-2 md:mb-4 animate-bounce">🎥</div>
                  <h3 className="text-lg md:text-xl font-bold text-red-400 mb-2">Metaverse Streaming</h3>
                  <p className="text-sm md:text-base text-gray-300">Live-Streams in der virtuellen Welt mit NFT-Zugang und Community-Voting!</p>
                </div>
                
                <div className="bg-black/40 backdrop-blur-lg rounded-xl p-4 md:p-6 border border-purple-500/30 hover:border-purple-500/60 transition-all duration-300 transform hover:scale-105 hover:rotate-1">
                  <div className="text-3xl md:text-4xl mb-2 md:mb-4 animate-pulse">🎁</div>
                  <h3 className="text-lg md:text-xl font-bold text-purple-400 mb-2">Airdrop Zone</h3>
                  <p className="text-sm md:text-base text-gray-300">Täglich MURAT Token claimen und exklusive Belohnungen erhalten!</p>
                </div>
                
                <div className="bg-black/40 backdrop-blur-lg rounded-xl p-4 md:p-6 border border-green-500/30 hover:border-green-500/60 transition-all duration-300 transform hover:scale-105 hover:-rotate-1">
                  <div className="text-3xl md:text-4xl mb-2 md:mb-4 animate-wiggle">🎮</div>
                  <h3 className="text-lg md:text-xl font-bold text-green-400 mb-2">Bitcoin-Jagd</h3>
                  <p className="text-sm md:text-base text-gray-300">Episches Adventure-Game mit Story-Entscheidungen und Reputation-System!</p>
                </div>
                
                <div className="bg-black/40 backdrop-blur-lg rounded-xl p-4 md:p-6 border border-yellow-500/30 hover:border-yellow-500/60 transition-all duration-300 transform hover:scale-105 hover:rotate-1">
                  <div className="text-3xl md:text-4xl mb-2 md:mb-4 animate-spin">🎭</div>
                  <h3 className="text-lg md:text-xl font-bold text-yellow-400 mb-2">NFT Marketplace</h3>
                  <p className="text-sm md:text-base text-gray-300">Sammle, handle und verkaufe einzigartige NFTs mit MURAT Token!</p>
                </div>

                <div className="bg-black/40 backdrop-blur-lg rounded-xl p-4 md:p-6 border border-pink-500/30 hover:border-pink-500/60 transition-all duration-300 transform hover:scale-105 hover:-rotate-1">
                  <div className="text-3xl md:text-4xl mb-2 md:mb-4 animate-bounce">🤖</div>
                  <h3 className="text-lg md:text-xl font-bold text-pink-400 mb-2">AI Creator</h3>
                  <p className="text-sm md:text-base text-gray-300">Generiere Memes, Comics und Content mit KI-Power!</p>
                </div>
              </div>
              
              {/* Animated Call-to-Action Button */}
              <div className="relative">
                <button
                  onClick={() => open()}
                  disabled={loading}
                  className="relative bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 hover:from-orange-600 hover:via-red-600 hover:to-pink-600 text-white font-bold py-4 md:py-6 px-8 md:px-12 rounded-2xl text-xl md:text-2xl transition-all duration-300 transform hover:scale-110 disabled:opacity-50 animate-glow shadow-2xl"
                >
                  {loading ? (
                    <span className="flex items-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                      Verbinde...
                    </span>
                  ) : (
                    <span className="flex items-center">
                      🚀 JETZT EINSTEIGEN! 🚀
                    </span>
                  )}
                </button>
                
                {/* Pulsing rings around button */}
                <div className="absolute inset-0 rounded-2xl animate-ping bg-gradient-to-r from-orange-500/20 via-red-500/20 to-pink-500/20"></div>
                <div className="absolute inset-0 rounded-2xl animate-pulse bg-gradient-to-r from-orange-500/10 via-red-500/10 to-pink-500/10"></div>
              </div>

              {/* Animated Text Below Button */}
              <div className="mt-6 text-center">
                <p className="text-white text-lg md:text-xl animate-pulse">
                  💫 <span className="text-yellow-300 font-bold">Wallet verbinden</span> und in die <span className="text-purple-300 font-bold">Zukunft starten!</span> 💫
                </p>
                <p className="text-gray-300 text-sm md:text-base mt-2 animate-bounce">
                  🎯 Polygon-Netzwerk | 🏆 MURAT Token | 🌐 Web3-Powered
                </p>
              </div>
            </div>

            {/* Floating Elements */}
            <div className="absolute top-20 left-10 text-4xl animate-bounce opacity-60">₿</div>
            <div className="absolute top-40 right-20 text-3xl animate-pulse opacity-50">🚀</div>
            <div className="absolute bottom-40 left-20 text-5xl animate-spin-slow opacity-40">🌟</div>
            <div className="absolute bottom-20 right-10 text-4xl animate-bounce opacity-60">💎</div>
          </div>
        ) : (
          <div>
            <MobileNavigation 
              isMobile={isMobile}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
            />

            {activeTab === 'dashboard' && (
              <Dashboard 
                tokenBalance={tokenBalance}
                stakingPositions={stakingPositions}
                nftAccess={nftAccess}
              />
            )}

            {activeTab === 'story' && (
              <StoryGame 
                address={address}
                apiBase={API_BASE}
              />
            )}

            {activeTab === 'staking' && (
              <StakingPanel 
                onCreatePosition={createStakingPosition}
                stakingPositions={stakingPositions}
                loading={loading}
              />
            )}

            {activeTab === 'streaming' && (
              <StreamingPanel 
                address={address}
                apiBase={API_BASE}
                loading={loading}
              />
            )}

            {activeTab === 'ai' && (
              <AICreator 
                onGenerateContent={generateAIContent}
                loading={loading}
              />
            )}

            {activeTab === 'nft' && (
              <NFTAccessPanel 
                nftAccess={nftAccess}
              />
            )}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}