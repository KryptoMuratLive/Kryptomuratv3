'use client';

import { formatAddress } from '@/lib/utils';

interface HeaderProps {
  isConnected: boolean;
  address?: string;
  tokenBalance: string;
  onConnectWallet: () => void;
  loading: boolean;
  isMobile: boolean;
  showMobileMenu: boolean;
  setShowMobileMenu: (show: boolean) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function Header({
  isConnected,
  address,
  tokenBalance,
  onConnectWallet,
  loading,
  isMobile,
  showMobileMenu,
  setShowMobileMenu,
  activeTab,
  setActiveTab
}: HeaderProps) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'metaverse', label: 'Metaverse', icon: '🌐' },
    { id: 'story', label: 'Bitcoin-Jagd', icon: '🎮' },
    { id: 'staking', label: 'Staking', icon: '🏦' },
    { id: 'streaming', label: 'Live Stream', icon: '🎥' },
    { id: 'ai', label: 'AI Creator', icon: '🤖' },
    { id: 'nft', label: 'NFT Access', icon: '🎭' }
  ];

  return (
    <header className={`${isMobile ? 'mobile-header' : 'desktop-header'} bg-black/20 backdrop-blur-lg border-b border-purple-500/20`}>
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 md:w-12 md:h-12 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              <span className="text-xl md:text-2xl font-bold text-black">₿</span>
            </div>
            <h1 className="text-lg md:text-2xl font-bold text-white">KryptoMurat</h1>
          </div>
          
          {/* Mobile Menu Button */}
          {isMobile && (
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="md:hidden text-white text-2xl focus:outline-none"
            >
              {showMobileMenu ? '✕' : '☰'}
            </button>
          )}
          
          {/* Desktop Wallet Info */}
          {!isMobile && (
            <div className="flex items-center space-x-4">
              {isConnected ? (
                <div className="flex items-center space-x-4">
                  <div className="bg-green-500/20 border border-green-500/30 rounded-lg px-3 py-1">
                    <span className="text-green-400 text-sm">{formatAddress(address || '')}</span>
                  </div>
                  <div className="bg-purple-500/20 border border-purple-500/30 rounded-lg px-3 py-1">
                    <span className="text-purple-400 text-sm">{parseFloat(tokenBalance).toFixed(2)} MURAT</span>
                  </div>
                </div>
              ) : (
                <button
                  onClick={onConnectWallet}
                  disabled={loading}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50"
                >
                  {loading ? 'Verbinde...' : 'Wallet Verbinden'}
                </button>
              )}
            </div>
          )}
        </div>
        
        {/* Mobile Wallet Info */}
        {isMobile && isConnected && (
          <div className="mt-3 flex items-center justify-between">
            <div className="bg-green-500/20 border border-green-500/30 rounded-lg px-3 py-1">
              <span className="text-green-400 text-xs">{formatAddress(address || '')}</span>
            </div>
            <div className="bg-purple-500/20 border border-purple-500/30 rounded-lg px-3 py-1">
              <span className="text-purple-400 text-xs">{parseFloat(tokenBalance).toFixed(2)} MURAT</span>
            </div>
          </div>
        )}
      </div>

      {/* Mobile Menu Overlay */}
      {isMobile && showMobileMenu && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 md:hidden">
          <div className="fixed top-0 right-0 w-64 h-full bg-gray-900 border-l border-purple-500/20 p-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-white font-semibold">Menu</h2>
              <button
                onClick={() => setShowMobileMenu(false)}
                className="text-white text-xl"
              >
                ✕
              </button>
            </div>
            
            {!isConnected && (
              <button
                onClick={() => {
                  onConnectWallet();
                  setShowMobileMenu(false);
                }}
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold py-3 px-4 rounded-lg mb-4 disabled:opacity-50"
              >
                {loading ? 'Verbinde...' : 'Wallet Verbinden'}
              </button>
            )}
            
            {/* Mobile Tab Navigation */}
            <div className="space-y-2">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setShowMobileMenu(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-purple-500/30 text-purple-400 border border-purple-500/50'
                      : 'text-gray-400 hover:bg-black/30'
                  }`}
                >
                  <span className="text-xl">{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}